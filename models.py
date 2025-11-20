from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------------------
# USERS
# ---------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, manager, employee, user
    password_hash = db.Column(db.String(255), nullable=False)

    telegram_id = db.Column(db.String(50))   # optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tasks_assigned = db.relationship("IjroTask", backref="assignee", lazy=True)

    def __repr__(self):
        return f"<User {self.full_name}>"


# ---------------------
# IJRO TASKS (ASSIGNEE BOR)
# ---------------------
class IjroTask(db.Model):
    __tablename__ = "ijro_tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")  # pending, in_progress, done, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # XATO YOZILGAN UCHUN SENDA ERROR CHIQARDI – YANGISI TO‘G‘RI
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<IjroTask {self.title}>"


# ---------------------
# EMPLOYEE TASKS (odamga biriktirilgan)
# ---------------------
class EmployeeTask(db.Model):
    __tablename__ = "employee_tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmployeeTask {self.title}>"


# ---------------------
# CONTRACTS (shartnomalar)
# ---------------------
class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    contract_number = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------
# VEHICLES (avtomobillar)
# ---------------------
class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50))
    model = db.Column(db.String(255))
    driver_name = db.Column(db.String(255))


# ---------------------
# WAREHOUSE (ombor)
# ---------------------
class WarehouseItem(db.Model):
    __tablename__ = "warehouse_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------
# ANALYTICS LOGS (optional)
# ---------------------
class AnalyticsLog(db.Model):
    __tablename__ = "analytics_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255))
    user_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
