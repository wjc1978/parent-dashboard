from flask import Flask, render_template, redirect, url_for, flash
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





@app.route("/")
@login_required
def dashboard():
    bp_logs = BPLog.query.filter_by(user_id=current_user.id).order_by(BPLog.created_at.desc()).limit(10).all()
    sodium_logs = SodiumLog.query.filter_by(user_id=current_user.id).order_by(SodiumLog.created_at.desc()).limit(10).all()
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date.asc()).all()
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).limit(5).all()
    moods = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.created_at.desc()).limit(7).all()

    chart_logs = list(reversed(bp_logs))
    labels = [log.created_at.strftime("%m-%d") for log in chart_logs]
    systolic = [log.systolic for log in chart_logs]
    diastolic = [log.diastolic for log in chart_logs]

    return render_template("dashboard.html", bp_logs=bp_logs, sodium_logs=sodium_logs,
                           tasks=tasks, notes=notes, moods=moods,
                           labels=labels, systolic=systolic, diastolic=diastolic)

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
        else:
            user = User(email=form.email.data,
                        password=generate_password_hash(form.password.data))
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

@app.route("/bp", methods=["GET","POST"])
@login_required
def bp():
    form = BPForm()
    if form.validate_on_submit():
        log = BPLog(user_id=current_user.id,
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
        log = SodiumLog(user_id=current_user.id,
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
        task = Task(user_id=current_user.id,
                    description=form.description.data,
                    date=form.date.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("tasks"))
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date.asc()).all()
    return render_template("tasks.html", form=form, tasks=tasks)

@app.route("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return redirect(url_for("tasks"))
    task.is_done = not task.is_done
    db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/notes", methods=["GET","POST"])
@login_required
def notes():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.id, text=form.text.data)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("notes"))
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return render_template("notes.html", form=form, notes=notes)

@app.route("/mood", methods=["GET","POST"])
@login_required
def mood():
    form = MoodForm()
    if form.validate_on_submit():
        log = MoodLog(user_id=current_user.id, mood_value=form.mood_value.data)
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
            user_id=current_user.id,
            title=form.title.data,
            date=form.date.data,
            time=form.time.data,
            notes=form.notes.data
        )
        db.session.add(appt)
        db.session.commit()
        return redirect(url_for("appointments"))
    appts = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.asc()).all()
    return render_template("appointments.html", form=form, appts=appts)

@app.route("/meds", methods=["GET","POST"])
@login_required
def meds():
    form = MedicationForm()
    if form.validate_on_submit():
        med = Medication(
            user_id=current_user.id,
            name=form.name.data,
            dose=form.dose.data,
            time=form.time.data,
            notes=form.notes.data
        )
        db.session.add(med)
        db.session.commit()
        return redirect(url_for("meds"))
    meds = Medication.query.filter_by(user_id=current_user.id).all()
    return render_template("meds.html", form=form, meds=meds)

if __name__ == "__main__":
    app.run(debug=True)
