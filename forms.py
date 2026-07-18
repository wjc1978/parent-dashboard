from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")

class BPForm(FlaskForm):
    systolic = IntegerField("Systolic", validators=[DataRequired()])
    diastolic = IntegerField("Diastolic", validators=[DataRequired()])
    submit = SubmitField("Save")

class SodiumForm(FlaskForm):
    amount_mg = IntegerField("Sodium (mg)", validators=[DataRequired()])
    submit = SubmitField("Save")

class TaskForm(FlaskForm):
    description = StringField("Task", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    submit = SubmitField("Add")

class NoteForm(FlaskForm):
    text = TextAreaField("Note", validators=[DataRequired()])
    submit = SubmitField("Save")

class MoodForm(FlaskForm):
    mood_value = SelectField(
    "Mood",
    choices=[
        ("happy", "Happy"),
        ("okay", "Okay"),
        ("sad", "Sad")
    ],
    validators=[DataRequired()]
)

class AppointmentForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    time = StringField("Time", validators=[DataRequired()])
    notes = TextAreaField("Notes")
    submit = SubmitField("Add Appointment")

class MedicationForm(FlaskForm):
    name = StringField("Medication", validators=[DataRequired()])
    dose = StringField("Dose", validators=[DataRequired()])
    time = StringField("Time", validators=[DataRequired()])
    notes = TextAreaField("Notes")
    submit = SubmitField("Add Medication")
