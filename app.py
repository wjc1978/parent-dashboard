import json
import secrets
import string
from datetime import date, datetime

from flask import Flask, render_template, redirect, url_for, flash, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, BPLog, SodiumLog, Task, Note, MoodLog, Appointment, Medication
from forms import LoginForm, RegisterForm, BPForm, SodiumForm, TaskForm, NoteForm, MoodForm, AppointmentForm, MedicationForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()
    
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_share_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if not User.query.filter_by(share_code=code).first():
            return code





@app.route("/")
@login_required
def dashboard():
    bp_logs = BPLog.query.filter_by(user_id=current_user.data_owner_id()).order_by(BPLog.created_at.desc()).limit(10).all()
    sodium_logs = SodiumLog.query.filter_by(user_id=current_user.data_owner_id()).order_by(SodiumLog.created_at.desc()).limit(10).all()
    tasks = Task.query.filter_by(user_id=current_user.data_owner_id()).order_by(Task.date.asc()).all()
    notes = Note.query.filter_by(user_id=current_user.data_owner_id()).order_by(Note.created_at.desc()).limit(5).all()
    moods = MoodLog.query.filter_by(user_id=current_user.data_owner_id()).order_by(MoodLog.created_at.desc()).limit(7).all()

    todays_appointments = Appointment.query.filter_by(user_id=current_user.data_owner_id(), date=date.today()).order_by(Appointment.time.asc()).all()
    todays_meds = Medication.query.filter_by(user_id=current_user.data_owner_id()).order_by(Medication.time.asc()).all()

    chart_logs = list(reversed(bp_logs))
    labels = [log.created_at.strftime("%m-%d") for log in chart_logs]
    systolic = [log.systolic for log in chart_logs]
    diastolic = [log.diastolic for log in chart_logs]

    sodium_chart_logs = list(reversed(sodium_logs))
    sodium_labels = [log.created_at.strftime("%m-%d") for log in sodium_chart_logs]
    sodium_amounts = [log.amount_mg for log in sodium_chart_logs]

    return render_template("dashboard.html", bp_logs=bp_logs, sodium_logs=sodium_logs,
                           tasks=tasks, notes=notes, moods=moods,
                           labels=labels, systolic=systolic, diastolic=diastolic,
                           sodium_labels=sodium_labels, sodium_amounts=sodium_amounts,
                           todays_appointments=todays_appointments, todays_meds=todays_meds)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html", form=form)

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered")
        elif form.role.data == "caregiver" and not form.share_code.data.strip():
            flash("Caregivers must enter a share code")
        else:
            user = User(email=form.email.data,
                        password=generate_password_hash(form.password.data),
                        role=form.role.data)
            if form.role.data == "caregiver":
                parent = User.query.filter_by(share_code=form.share_code.data.strip().upper(), role="parent").first()
                if not parent:
                    flash("Invalid caregiver share code")
                    return render_template("register.html", form=form)
                user.parent_id = parent.id
            else:
                user.share_code = generate_share_code()
            db.session.add(user)
            db.session.commit()
            flash("Registered, please log in")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/account")
@login_required
def account():
    parent = None
    if current_user.role == "caregiver" and current_user.parent_id:
        parent = User.query.get(current_user.parent_id)
    caregivers = []
    if current_user.role == "parent":
        caregivers = User.query.filter_by(parent_id=current_user.id).all()
    return render_template("account.html", parent=parent, caregivers=caregivers)

@app.route("/backup")
@login_required
def backup():
    owner_id = current_user.data_owner_id()

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "bp_logs": [
            {"systolic": r.systolic, "diastolic": r.diastolic, "created_at": r.created_at.isoformat()}
            for r in BPLog.query.filter_by(user_id=owner_id).all()
        ],
        "sodium_logs": [
            {"amount_mg": r.amount_mg, "created_at": r.created_at.isoformat()}
            for r in SodiumLog.query.filter_by(user_id=owner_id).all()
        ],
        "tasks": [
            {"description": r.description, "is_done": r.is_done, "date": r.date.isoformat()}
            for r in Task.query.filter_by(user_id=owner_id).all()
        ],
        "notes": [
            {"text": r.text, "created_at": r.created_at.isoformat()}
            for r in Note.query.filter_by(user_id=owner_id).all()
        ],
        "moods": [
            {"mood_value": r.mood_value, "created_at": r.created_at.isoformat()}
            for r in MoodLog.query.filter_by(user_id=owner_id).all()
        ],
        "appointments": [
            {"title": r.title, "date": r.date.isoformat(), "time": r.time, "notes": r.notes}
            for r in Appointment.query.filter_by(user_id=owner_id).all()
        ],
        "medications": [
            {"name": r.name, "dose": r.dose, "time": r.time, "notes": r.notes}
            for r in Medication.query.filter_by(user_id=owner_id).all()
        ],
    }

    filename = f"parent-dashboard-backup-{date.today().isoformat()}.json"
    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/restore", methods=["GET", "POST"])
@login_required
def restore():
    if request.method == "POST":
        file = request.files.get("backup_file")
        if not file or not file.filename:
            flash("Choose a backup file first")
            return redirect(url_for("restore"))
        try:
            data = json.load(file.stream)
        except (json.JSONDecodeError, UnicodeDecodeError):
            flash("That file isn't valid backup JSON")
            return redirect(url_for("restore"))

        owner_id = current_user.data_owner_id()
        added = 0

        for r in data.get("bp_logs", []):
            db.session.add(BPLog(user_id=owner_id, systolic=r["systolic"], diastolic=r["diastolic"],
                                  created_at=datetime.fromisoformat(r["created_at"])))
            added += 1
        for r in data.get("sodium_logs", []):
            db.session.add(SodiumLog(user_id=owner_id, amount_mg=r["amount_mg"],
                                      created_at=datetime.fromisoformat(r["created_at"])))
            added += 1
        for r in data.get("tasks", []):
            db.session.add(Task(user_id=owner_id, description=r["description"], is_done=r["is_done"],
                                 date=date.fromisoformat(r["date"])))
            added += 1
        for r in data.get("notes", []):
            db.session.add(Note(user_id=owner_id, text=r["text"],
                                 created_at=datetime.fromisoformat(r["created_at"])))
            added += 1
        for r in data.get("moods", []):
            db.session.add(MoodLog(user_id=owner_id, mood_value=r["mood_value"],
                                    created_at=datetime.fromisoformat(r["created_at"])))
            added += 1
        for r in data.get("appointments", []):
            db.session.add(Appointment(user_id=owner_id, title=r["title"], date=date.fromisoformat(r["date"]),
                                        time=r["time"], notes=r.get("notes")))
            added += 1
        for r in data.get("medications", []):
            db.session.add(Medication(user_id=owner_id, name=r["name"], dose=r["dose"],
                                       time=r["time"], notes=r.get("notes")))
            added += 1

        db.session.commit()
        flash(f"Restored {added} records")
        return redirect(url_for("dashboard"))

    return render_template("restore.html")

@app.route("/bp", methods=["GET","POST"])
@login_required
def bp():
    form = BPForm()
    if form.validate_on_submit():
        log = BPLog(user_id=current_user.data_owner_id(),
                    systolic=form.systolic.data,
                    diastolic=form.diastolic.data)
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("bp.html", form=form)

@app.route("/sodium", methods=["GET","POST"])
@login_required
def sodium():
    form = SodiumForm()
    if form.validate_on_submit():
        log = SodiumLog(user_id=current_user.data_owner_id(),
                        amount_mg=form.amount_mg.data)
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("sodium.html", form=form)

@app.route("/tasks", methods=["GET","POST"])
@login_required
def tasks():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(user_id=current_user.data_owner_id(),
                    description=form.description.data,
                    date=form.date.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("tasks"))
    tasks = Task.query.filter_by(user_id=current_user.data_owner_id()).order_by(Task.date.asc()).all()
    return render_template("tasks.html", form=form, tasks=tasks)

@app.route("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.data_owner_id():
        return redirect(url_for("tasks"))
    task.is_done = not task.is_done
    db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/notes", methods=["GET","POST"])
@login_required
def notes():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.data_owner_id(), text=form.text.data)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("notes"))
    notes = Note.query.filter_by(user_id=current_user.data_owner_id()).order_by(Note.created_at.desc()).all()
    return render_template("notes.html", form=form, notes=notes)

@app.route("/mood", methods=["GET","POST"])
@login_required
def mood():
    form = MoodForm()
    if form.validate_on_submit():
        log = MoodLog(user_id=current_user.data_owner_id(), mood_value=form.mood_value.data)
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("mood.html", form=form)

@app.route("/appointments", methods=["GET","POST"])
@login_required
def appointments():
    form = AppointmentForm()
    if form.validate_on_submit():
        appt = Appointment(
            user_id=current_user.data_owner_id(),
            title=form.title.data,
            date=form.date.data,
            time=form.time.data,
            notes=form.notes.data
        )
        db.session.add(appt)
        db.session.commit()
        return redirect(url_for("appointments"))
    appts = Appointment.query.filter_by(user_id=current_user.data_owner_id()).order_by(Appointment.date.asc()).all()
    return render_template("appointments.html", form=form, appts=appts)

@app.route("/meds", methods=["GET","POST"])
@login_required
def meds():
    form = MedicationForm()
    if form.validate_on_submit():
        med = Medication(
            user_id=current_user.data_owner_id(),
            name=form.name.data,
            dose=form.dose.data,
            time=form.time.data,
            notes=form.notes.data
        )
        db.session.add(med)
        db.session.commit()
        return redirect(url_for("meds"))
    meds = Medication.query.filter_by(user_id=current_user.data_owner_id()).all()
    return render_template("meds.html", form=form, meds=meds)

if __name__ == "__main__":
    app.run(debug=True)
