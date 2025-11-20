from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# -----------------------
# USER MODEL
# -----------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(300))
    role = db.Column(db.String(50))   # admin, manager, employee, user
    telegram = db.Column(db.String(100))

    # Relationship: user → tasks assigned to him
    tasks = db.relationship("Task", back_populates="assignee", lazy=True)


# -----------------------
# TASK MODEL
# -----------------------
class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")  # pending / in_progress / done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)

    # Who created the task (manager/admin)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Who must execute (employee)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Relationships
    creator = db.relationship("User", foreign_keys=[creator_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id], back_populates="tasks")
