from flask import Flask, render_template, request, redirect, session, flash, url_for

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate

from datetime import timedelta

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
    name = db.Column(db.String(80), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False, default="changeme") 
    created_at = db.Column(db.DateTime, default=datetime.now)
    acknowledged = db.Column(db.Boolean, default=False) 


    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    tags = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    due_date = db.Column(db.DateTime)
    reminder_datetime = db.Column(db.DateTime)  # <-- ADD THIS
    completed_at = db.Column(db.DateTime)
    dismissed = db.Column(db.Boolean, default=False)

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


def get_user():
    if "username" in session:
        return User.query.filter_by(username=session["username"]).first()
    return None


@app.route("/add")
def add_page():
    user = get_user()
    if not user:
        return redirect("/")

    task_id = request.args.get("task_id")
    task = None
    if task_id:
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()

    return render_template("add.html", task=task)


@app.route("/tasks/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if not task:
            return redirect("/")

        task.task = request.form["task"]
        task.tags = request.form.get("tags")
        priority = request.form.get("priority")
        task.priority = TaskPriority(priority) if priority else TaskPriority.MEDIUM

        # Due date
        date_due = request.form.get("date_due")
        time_due = request.form.get("time_due")
        if date_due:
            try:
                if time_due:
                    task.due_date = datetime.strptime(f"{date_due} {time_due}", "%Y-%m-%d %H:%M")
                else:
                    task.due_date = datetime.strptime(date_due, "%Y-%m-%d")
            except ValueError:
                task.due_date = None
        else:
            task.due_date = None

        # Reminder
        reminder = request.form.get("reminder_datetime")
        if reminder:
            try:
                task.reminder_datetime = datetime.strptime(reminder, "%Y-%m-%dT%H:%M")
                task.dismissed = False
            except ValueError:
                task.reminder_datetime = None
        else:
            task.reminder_datetime = None

        db.session.commit()

    return redirect("/")



@app.route('/dismiss/<int:task_id>', methods=['POST'])
def dismiss_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if not task:
            return {"success": False, "error": "Task not found"}, 404

        task.dismissed = True  # Mark as dismissed
        db.session.commit()
        return {"success": True}
    return {"success": False}, 401


@app.route('/snooze/<int:task_id>', methods=['POST'])
def snooze_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if not task:
            return {"success": False, "error": "Task not found"}, 404

        task.reminder_datetime = datetime.now() + timedelta(minutes=5)
        task.dismissed = False
        task.acknowledged = False 
        db.session.commit()

        return {"success": True, "new_reminder": task.reminder_datetime.isoformat()}
    return {"success": False}, 401

from flask import jsonify
from datetime import datetime, timedelta

@app.route("/check_reminders")
def check_reminders():
    """Return the first pending reminder that is due or overdue."""
    if user := get_user():
        now = datetime.now()

        task = (
                Task.query.filter(
                Task.user_id == user.id,
                Task.completed_at.is_(None),
                Task.dismissed == False,
                Task.acknowledged == False,   # <-- NEW
                Task.reminder_datetime.isnot(None),
                Task.reminder_datetime <= now,
            )
             .order_by(Task.reminder_datetime.asc())
            .first()
        )
        if task:
            return jsonify({
                "reminder": True,
                "task_id": task.id,
                "task": task.task,
            })
    return jsonify({"reminder": False})

@app.route("/api/tasks/<int:task_id>/stop", methods=["POST"])
def stop_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task.acknowledged = True
        db.session.commit()
        return jsonify({"message": "Task stopped"}), 200
    return jsonify({"error": "Task not found"}), 404



@app.route("/api/pending_reminders")
def api_pending_reminders():
    if user := get_user():
        tasks = Task.query.filter_by(user_id=user.id, completed_at=None, dismissed=False).all()
        result = [
            {
                "id": task.id,
                "title": task.task,
                "reminder_datetime": task.reminder_datetime.isoformat() if task.reminder_datetime else None
            }
            for task in tasks if task.reminder_datetime
        ]
        return {"tasks": result}
    return {"tasks": []}



@app.route("/", methods=['GET', 'POST'])
def homepage():
    error_text = ""
    user = get_user()

    # --- LOGIN HANDLING ---
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error_text = "Username or password cannot be empty"
        else:
            user = User.query.filter_by(username=username).first()
            if not user:
                flash("User with username does not exist!", "error")
                return redirect(url_for("create_account"))
            if user.password != password:
                error_text = "Username or password is not correct"

        if error_text:
            return render_template("index.html", error_text=error_text)

        # Login user
        session['username'] = user.username

    if not user:
        error_text = "You must be logged in to continue"
        return render_template("index.html", error_text=error_text)

    # --- SEARCH & FILTER ---
    search_query = request.args.get("search", "").strip()
    filter_query = request.args.get("filter", "").strip()

    tasks_query = Task.query.filter_by(user_id=user.id)

    if filter_query in ["low", "medium", "high"]:
        tasks_query = tasks_query.filter(Task.priority == TaskPriority(filter_query))
    elif filter_query == "completed":
        tasks_query = tasks_query.filter(Task.completed_at.isnot(None))
    elif filter_query == "pending":
        tasks_query = tasks_query.filter(Task.completed_at.is_(None))

    if search_query:
        tasks_query = tasks_query.filter(Task.task.ilike(f"%{search_query}%"))

    tasks = tasks_query.order_by(Task.created_at.desc()).all()

    # --- CLASSIFY TASKS ---
    pending_tasks = [task for task in tasks if not task.is_completed]
    completed_tasks = [task for task in tasks if task.is_completed]

    # --- ADD ICON & TIME DISPLAY ---
    for task in pending_tasks + completed_tasks:
        if task.reminder_datetime:
            task.display_icon = "fa-bell"
            task.display_time = task.reminder_datetime.strftime('%d-%m-%Y %H:%M')
        elif task.due_date:
            task.display_icon = "fa-calendar"
            task.display_time = task.due_date.strftime('%d-%m-%Y %H:%M')
        else:
            task.display_icon = None
            task.display_time = None

    return render_template("home.html", pending_tasks=pending_tasks, completed_tasks=completed_tasks)



@app.route("/create-account", methods=['GET', 'POST'])
def create_account():
    if request.method == "POST":
        name = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')

        user = User()
        user.name = name
        user.username = username
        user.password = password

        db.session.add(user)
        db.session.commit()

        session['username'] = username

        return redirect("/")
    
    return render_template("create_account.html")


@app.route("/logout")
def logout():
    try:
        session.pop("username")

    except Exception as e:
        print(f"Error during logout: {e}")

    finally:
        return redirect("/")


@app.route("/tasks/new", methods=["POST"])
def create_task():
    if user := get_user():
        task_desc = request.form["task"]
        date_due = request.form.get("date_due")
        time_due = request.form.get("time_due")
        priority = request.form.get("priority")
        tags = request.form.get("tags")
        reminder = request.form.get("reminder_datetime")

        # Combine date and time
        due_datetime = None
        if date_due:
            try:
                if time_due:
                    due_datetime = datetime.strptime(f"{date_due} {time_due}", "%Y-%m-%d %H:%M")
                else:
                    due_datetime = datetime.strptime(date_due, "%Y-%m-%d")
            except ValueError:
                due_datetime = None

        # Parse reminder
        reminder_datetime = None
        dismissed = True
        if reminder:
            try:
                reminder_datetime = datetime.strptime(reminder, "%Y-%m-%dT%H:%M")
                dismissed = False
            except ValueError:
                reminder_datetime = None

        # Save new task
        if user and task_desc:
            new_task = Task(
                task=task_desc,
                due_date=due_datetime,
                reminder_datetime=reminder_datetime,
                dismissed=dismissed,
                user_id=user.id,
                priority=TaskPriority(priority) if priority else TaskPriority.MEDIUM,
                tags=tags
            )
            db.session.add(new_task)
            db.session.commit()

    return redirect("/")


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if task:
            task.completed_at = datetime.now()
            db.session.commit()

    return redirect("/")


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if task:
            db.session.delete(task)
            db.session.commit()

    return redirect("/")


@app.route("/tasks/<int:task_id>/reopen", methods=["POST"])
def reopen_task(task_id):
    if user := get_user():
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        if task:
            task.completed_at = None
            db.session.commit()

    return redirect("/")


@app.route("/tasks/clear/", methods=["POST"])
def clear_completed_tasks():
    if user := get_user():
        all_tasks = Task.query.filter_by(user_id=user.id).all()
        for task in all_tasks:
            db.session.delete(task)
        db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

