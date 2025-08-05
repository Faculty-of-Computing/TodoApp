from flask import Flask, render_template, request, redirect, session

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate

import os
import random
import string

from datetime import datetime

from enum import Enum

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    tags = db.column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.task}>'
    
    @property
    def is_completed(self):
        return self.completed_at is not None
    

def generate_unique_username(base_username):
    username = base_username
    while User.query.filter_by(username=username).first() is not None:
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        username = f"{base_username}{suffix}"
    return username


@app.route("/", methods=['GET', 'POST'])
def homepage():
    error_text = ""

    if request.method == "POST":
        username = request.form.get("username", None)

        if username:
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User()
                user.username = username
                db.session.add(user)
                db.session.commit()

            session["username"] = username

        else:
            error_text = "Username not present"

    if "username" in session:
        # Get all user tasks
        user = User.query.filter_by(username=session["username"]).first()
        if not user:
            return redirect("/logout")
        
        tasks = Task.query.filter_by(user_id=user.id).all()

        pending_tasks = [task for task in tasks if not task.is_completed]
        completed_tasks = [task for task in tasks if task.is_completed]

        return render_template("home.html", pending_tasks=pending_tasks, completed_tasks=completed_tasks)
    
    return render_template("index.html", error_text=error_text)


@app.route("/logout")
def logout():
    session.pop("username")

    return redirect("/")


@app.route("/tasks/new", methods=["POST"])
def create_task():
    if "username" in session:
        task_desc = request.form["task"]
        date_due = request.form.get("date_due")  # e.g., "2025-08-04"
        time_due = request.form.get("time_due")  # e.g., "14:30"
        priority = request.form.get("priority")
        tags = request.form.get("tags")

        # Combine date and time into a datetime object
        due_datetime = None
        if date_due:
            try:
                if time_due:
                    due_datetime = datetime.strptime(f"{date_due} {time_due}", "%Y-%m-%d %H:%M")
                else:
                    due_datetime = datetime.strptime(f"{date_due}", "%Y-%m-%d")

            except ValueError:
                due_datetime = None  # Handle invalid input as needed

        # Get user
        username = session.get("username")
        user = User.query.filter_by(username=username).first()

        # Create and save the task
        if user and task_desc:
            new_task = Task()

            new_task.task = task_desc,
            new_task.due_date = due_datetime,
            new_task.user_id = user.id
            new_task.priority = priority
            new_task.tags = tags
            
            db.session.add(new_task)
            db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
