from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# --- Users & roles ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="user")  # admin / manager / employee / user
    telegram_id = db.Column(db.String(64))

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

# --- Generic task (Topshriqlar moduli) ---

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default="new")  # new / in_progress / pending / done / rejected
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)

    creator = db.relationship("User", foreign_keys=[creator_id], backref="created_tasks")
    assignee = db.relationship("User", foreign_keys=[assignee_id], backref="assigned_tasks")

# --- Ijro moduli ---

class IjroTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(200))  # Prezident qarori, Vazirlik, va hokazo
    received_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(32), default="new")  # new / in_progress / pending / done / overdue
    executor_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # mas'ul ijrochi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    executor = db.relationship("User")

    @property
    def days_left(self) -> int:
        if not self.due_date:
            return 999
        return (self.due_date - date.today()).days

# --- Avto transport ---

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(32), unique=True, nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer)
    last_repair_date = db.Column(db.Date)
    contract_ref = db.Column(db.String(128))
    defect_act_ref = db.Column(db.String(128))
    driver_name = db.Column(db.String(128))
    driver_phone = db.Column(db.String(32))
    monthly_fuel_limit = db.Column(db.Float, default=0.0)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))

# --- Organization / Tashkilotlar ---

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    employee_count = db.Column(db.Integer, default=0)
    logo_filename = db.Column(db.String(255))
    address = db.Column(db.String(255))
    building_size = db.Column(db.String(64))

    vehicles = db.relationship("Vehicle", backref="organization", lazy=True)

# --- Outsourcing ---

class OutsourcingCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contract_number = db.Column(db.String(64))
    contract_date = db.Column(db.Date)
    valid_until = db.Column(db.Date)
    services = db.Column(db.Text)

# --- Office / org texnika (OrgTech moduli sifatida) ---

class OrgTech(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    inventory_number = db.Column(db.String(64))
    location = db.Column(db.String(128))
    responsible_person = db.Column(db.String(128))
    status = db.Column(db.String(64), default="active")

# --- Contracts / Shartnomalar ---

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(64))
    title = db.Column(db.String(200), nullable=False)
    partner = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    signed_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(64), default="active")  # active / completed / overdue
    file_name = db.Column(db.String(255))

# --- Solar sites (Quyosh panelari) ---

class SolarSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(255))
    installed_power_kw = db.Column(db.Float, default=0.0)
    installed_date = db.Column(db.Date)
    energy_kwh = db.Column(db.Float, default=0.0)

# --- Employee profiles (Xodimlar moduli) ---

class EmployeeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    position = db.Column(db.String(128))
    department = db.Column(db.String(128))
    resume_file = db.Column(db.String(255))

# --- Bino va Yashil makon modullari ---

class Building(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(128))  # ofis, ombor, filial
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(255))
    info = db.Column(db.Text)

class GreenArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(128))
    name = db.Column(db.String(200), nullable=False)
    area_size = db.Column(db.String(64))
    planted_date = db.Column(db.Date)
    care_plan = db.Column(db.Text)

# --- Ombor va talabnomalar ---

class WarehouseProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(128))
    unit = db.Column(db.String(32))  # dona, kg, litr
    quantity = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class WarehouseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    department = db.Column(db.String(128))
    status = db.Column(db.String(32), default="new")  # new / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User")

class WarehouseRequestItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("warehouse_request.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("warehouse_product.id"), nullable=True)

    name = db.Column(db.String(200))
    unit = db.Column(db.String(32))
    ombordagi = db.Column(db.Float, default=0.0)
    soralgani = db.Column(db.Float, default=0.0)
    berilgani = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, default=0.0)

    request = db.relationship("WarehouseRequest", backref="items")
    product = db.relationship("WarehouseProduct")

# --- Mehmonlar ---

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(200))
    reason = db.Column(db.String(255))  # PQ-xxxx
    arrive_date = db.Column(db.Date)
    leave_date = db.Column(db.Date)
    services = db.Column(db.Text)  # restoran, sovg'a va hokazo
    total_amount = db.Column(db.Float, default=0.0)
    file_name = db.Column(db.String(255))

# --- Tabriknomalar ---

class Greeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), default="birthday")  # birthday / generic
    person = db.Column(db.String(200))
    date = db.Column(db.Date)
    description = db.Column(db.Text)

# --- Simple helper to create demo data ---

def seed_demo_data(db):
    if User.query.count() > 0:
        return
    from werkzeug.security import generate_password_hash

    admin = User(full_name="Super Admin", email="admin@example.com",
                 password_hash=generate_password_hash("admin123"), role="admin")
    manager = User(full_name="Rahbar", email="manager@example.com",
                   password_hash=generate_password_hash("manager123"), role="manager")
    employee = User(full_name="Xodim", email="employee@example.com",
                    password_hash=generate_password_hash("employee123"), role="employee")
    user = User(full_name="Ombor so'rovchi", email="user@example.com",
                password_hash=generate_password_hash("user123"), role="user")

    db.session.add_all([admin, manager, employee, user])
    db.session.commit()

    org = Organization(name="AF Bosh ofis", employee_count=50, address="Toshkent", building_size="3-qavat")
    db.session.add(org)
    db.session.commit()

    v1 = Vehicle(plate_number="01A123BC", model="Cobalt", year=2022, driver_name="Aliyev Anvar",
                 monthly_fuel_limit=150, organization_id=org.id)
    db.session.add(v1)

    c1 = Contract(number="SH-001", title="Elektr energiyasi shartnomasi",
                  partner="Hududiy elektr tarmoqlari", amount=18225670)
    db.session.add(c1)

    task1 = Task(title="Serverlarni tekshirish",
                 description="Yangi platformani stagingda sinash",
                 status="in_progress", assignee=employee, creator=manager)
    task2 = Task(title="Oy yakuniy hisobot", description="Excel hisobot tayyorlash",
                 status="new", assignee=employee, creator=manager)
    db.session.add_all([task1, task2])

    db.session.commit()
