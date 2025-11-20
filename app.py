import os
import csv
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import (
    db, User, Task, Vehicle, Organization, OutsourcingCompany, OrgTech,
    Contract, SolarSite, EmployeeProfile, IjroTask,
    WarehouseProduct, WarehouseRequest, WarehouseRequestItem,
    Guest, Greeting, Building, GreenArea, seed_demo_data
)

# -------------------------
#   APP INIT
# -------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Upload folder
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


# -------------------------
#  DATABASE INIT
# -------------------------
@app.route("/init-db")
def init_db():
    with app.app_context():
        db.create_all()
        seed_demo_data(db)
    return "Database created and demo data added."


# -------------------------
#         LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Login yoki parol xato", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=True)
        flash("Xush kelibsiz!", "success")

        if user.role == "admin":
            return redirect(url_for("admin_panel"))
        elif user.role == "manager":
            return redirect(url_for("manager_dashboard"))
        elif user.role == "employee":
            return redirect(url_for("employee_panel"))
        else:
            return redirect(url_for("user_panel"))

    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Chiqdingiz", "info")
    return redirect(url_for("login"))


# -------------------------
#       ADMIN
# -------------------------
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return redirect(url_for("login"))
    users = User.query.all()
    return render_template("admin/panel.html", users=users)


# ✔ yagona to‘g‘ri create-user route
@app.route("/admin/create-user", methods=["POST"])
@login_required
def admin_create_user():
    if current_user.role != "admin":
        return "Access denied", 403

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    role = request.form.get("role")
    password = request.form.get("password")

    if not password:
        password = "123456"

    if User.query.filter_by(email=email).first():
        flash("Bu email allaqachon mavjud", "warning")
        return redirect(url_for("admin_panel"))

    hashed = generate_password_hash(password)

    new_user = User(full_name=full_name, email=email, role=role, password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()

    flash("Yangi foydalanuvchi yaratildi!", "success")
    return redirect(url_for("admin_panel"))


# -------------------------
#  DEFAULT ROUTER
# -------------------------
@app.route("/")
@login_required
def index():
    if current_user.role == "admin":
        return redirect(url_for("admin_panel"))
    elif current_user.role == "manager":
        return redirect(url_for("manager_dashboard"))
    elif current_user.role == "employee":
        return redirect(url_for("employee_panel"))
    else:
        return redirect(url_for("user_panel"))


# -------------------------
#  MANAGER (Rahbar) panel
# -------------------------
@app.route("/manager/dashboard")
@login_required
def manager_dashboard():
    if current_user.role != "manager":
        return redirect(url_for("index"))

    total_tasks = Task.query.count()
    done_tasks = Task.query.filter_by(status="done").count()
    in_progress_tasks = Task.query.filter_by(status="in_progress").count()
    ijro_count = IjroTask.query.count()
    contracts_sum = db.session.query(db.func.coalesce(db.func.sum(Contract.amount), 0)).scalar()

    vehicles = Vehicle.query.all()
    employees = EmployeeProfile.query.count()
    guests = Guest.query.count()

    return render_template(
        "manager/dashboard.html",
        total_tasks=total_tasks,
        done_tasks=done_tasks,
        in_progress_tasks=in_progress_tasks,
        ijro_count=ijro_count,
        contracts_sum=int(contracts_sum or 0),
        vehicles=vehicles[:4],
        employees=employees,
        guests=guests,
    )


# -------------------------
#  USER PANEL
# -------------------------
@app.route("/user")
@login_required
def user_panel():
    if current_user.role != "user":
        return redirect(url_for("index"))
    requests_list = WarehouseRequest.query.filter_by(
        creator_id=current_user.id
    ).order_by(WarehouseRequest.created_at.desc()).all()

    return render_template("user/panel.html", requests=requests_list)


# -------------------------
#   LOCAL RUN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_demo_data(db)
    app.run(debug=True)
