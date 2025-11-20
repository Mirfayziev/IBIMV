import os
from datetime import datetime
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import (
    db, User, Task, Vehicle, Organization, OutsourcingCompany, OrgTech,
    Contract, SolarSite, EmployeeProfile, IjroTask,
    WarehouseProduct, WarehouseRequest, WarehouseRequestItem,
    Guest, Greeting, Building, GreenArea, seed_demo_data
)

# ======================================================
#   APP START
# ======================================================
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


# ======================================================
#   DATABASE AUTO INIT (KOYEB)
# ======================================================
with app.app_context():
    db.create_all()
    try:
        seed_demo_data(db)
    except:
        pass


# ======================================================
#                   LOGIN
# ======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Login yoki parol xato", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=True)

        flash("Xush kelibsiz!", "success")

        # ------------ ROLE REDIRECT 100% ✔ ------------
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


# ======================================================
#             HOME → ROLE REDIRECT
# ======================================================
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


# ======================================================
#                   ADMIN PANEL
# ======================================================
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("Bu bo‘limga faqat admin kira oladi", "warning")
        return redirect(url_for("index"))

    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/panel.html", users=users)


@app.route("/admin/create_user", methods=["POST"])
@login_required
def admin_create_user():
    if current_user.role != "admin":
        flash("Ruxsat yo‘q", "danger")
        return redirect(url_for("index"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "user")
    password = request.form.get("password", "").strip()

    if not password:
        password = "123456"

    if User.query.filter_by(email=email).first():
        flash("Bu email allaqachon mavjud", "warning")
        return redirect(url_for("admin_panel"))

    hashed = generate_password_hash(password)

    new_user = User(
        full_name=full_name,
        email=email,
        role=role,
        password_hash=hashed
    )
    db.session.add(new_user)
    db.session.commit()

    flash("Yangi foydalanuvchi yaratildi", "success")
    return redirect(url_for("admin_panel"))


# ======================================================
#                   MANAGER PANEL
# ======================================================
@app.route("/manager/dashboard")
@login_required
def manager_dashboard():
    if current_user.role != "manager":
        flash("Bu bo‘limga faqat rahbar kira oladi", "warning")
        return redirect(url_for("index"))

    total_tasks = Task.query.count()
    done_tasks = Task.query.filter_by(status="done").count()
    progress_tasks = Task.query.filter_by(status="in_progress").count()
    ijro_count = IjroTask.query.count()

    contracts_sum = db.session.query(
        db.func.coalesce(db.func.sum(Contract.amount), 0)
    ).scalar() or 0

    vehicles = Vehicle.query.all()
    employees_count = EmployeeProfile.query.count()
    guests_count = Guest.query.count()

    return render_template(
        "manager/dashboard.html",
        total_tasks=total_tasks,
        done_tasks=done_tasks,
        progress_tasks=progress_tasks,
        ijro_count=ijro_count,
        contracts_sum=int(contracts_sum),
        vehicles=vehicles[:4],
        employees_count=employees_count,
        guests_count=guests_count,
    )


# ======================================================
#                   EMPLOYEE PANEL
# ======================================================
@app.route("/employee")
@login_required
def employee_panel():
    if current_user.role != "employee":
        flash("Bu bo‘limga faqat xodim kira oladi", "warning")
        return redirect(url_for("index"))

    tasks = Task.query.filter_by(assignee_id=current_user.id).all()
    ijro_tasks = IjroTask.query.filter_by(assignee_id=current_user.id).all()
    return render_template("employee/panel.html", tasks=tasks, ijro_tasks=ijro_tasks)


@app.route("/employee/update_task_status/<int:task_id>", methods=["POST"])
@login_required
def employee_update_task_status(task_id):
    if current_user.role != "employee":
        flash("Ruxsat yo'q", "danger")
        return redirect(url_for("index"))

    task = Task.query.get(task_id)
    if not task or task.assignee_id != current_user.id:
        flash("Topshiriq topilmadi", "danger")
        return redirect(url_for("employee_panel"))

    new_status = request.form.get("status")
    if new_status not in ["in_progress", "pending", "done", "rejected"]:
        flash("Noto'g'ri status", "warning")
        return redirect(url_for("employee_panel"))

    task.status = new_status
    db.session.commit()

    flash("Topshiriq holati yangilandi", "success")
    return redirect(url_for("employee_panel"))


# ======================================================
#                   USER PANEL
# ======================================================
@app.route("/user")
@login_required
def user_panel():
    requests_list = WarehouseRequest.query.filter_by(
        creator_id=current_user.id
    ).order_by(WarehouseRequest.created_at.desc())

    return render_template("user/panel.html", requests=requests_list.all())


# ======================================================
#         PLACEHOLDERS (keyin to‘ldirasiz)
# ======================================================
@app.route("/ijro")
@login_required
def ijro_module():
    return "Ijro moduli ishlayapti"


@app.route("/warehouse")
@login_required
def warehouse_module():
    return "Ombor moduli ishlayapti"


@app.route("/orgtech")
@login_required
def orgtech_module():
    return "Org texnika moduli ishlayapti"


# ======================================================
#             LOCAL RUN (DEVELOPMENT)
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
