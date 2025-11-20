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

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}

@app.route("/init-db")
def init_db():
    db.create_all()
    seed_demo_data(db)
    return "Database created and demo data added."

# --- Auth ---

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
        # redirect by role
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

# --- Admin panel ---

@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return redirect(url_for("login"))
    users = User.query.all()
    return render_template("admin/panel.html", users=users)

@app.route("/admin/create-user", methods=["POST"])
@login_required
def admin_create_user():
    if current_user.role != "admin":
        return redirect(url_for("login"))
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    role = request.form.get("role")
    password = request.form.get("password") or "password123"
    if User.query.filter_by(email=email).first():
        flash("Bu email allaqachon mavjud", "warning")
    else:
        u = User(full_name=full_name, email=email,
                 role=role, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        flash("Foydalanuvchi yaratildi", "success")
    return redirect(url_for("admin_panel"))

# --- Route dispatcher ---

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

# --- Manager (Rahbar) dashboard ---

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

@app.route("/manager/vehicles")
@login_required
def manager_vehicles():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    vehicles = Vehicle.query.all()
    return render_template("vehicles/list.html", vehicles=vehicles)

@app.route("/manager/contracts")
@login_required
def manager_contracts():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    contracts = Contract.query.all()
    return render_template("contracts/list.html", contracts=contracts)

@app.route("/manager/ijro")
@login_required
def manager_ijro():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    tasks = IjroTask.query.order_by(IjroTask.due_date.asc()).all()
    today = date.today()
    return render_template("ijro/list.html", tasks=tasks, today=today)

# --- Org Texnika moduli (manager uchun) ---

@app.route("/manager/orgtech", methods=["GET", "POST"])
@login_required
def manager_orgtech():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name")
        inventory_number = request.form.get("inventory_number")
        category = request.form.get("category")
        location = request.form.get("location")
        responsible_person = request.form.get("responsible_person")
        if name:
            item = OrgTech(
                name=name,
                inventory_number=inventory_number,
                location=location,
                responsible_person=responsible_person,
                status=category or "active",
            )
            db.session.add(item)
            db.session.commit()
            flash("Org texnika qo'shildi", "success")
        return redirect(url_for("manager_orgtech"))
    items = OrgTech.query.order_by(OrgTech.id.desc()).all()
    return render_template("orgtech/list.html", items=items)

@app.route("/manager/orgtech/export")
@login_required
def manager_orgtech_export():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], "orgtech_export.csv")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["id", "name", "inventory_number", "location", "responsible_person", "status"])
        for i in OrgTech.query.order_by(OrgTech.id).all():
            writer.writerow([i.id, i.name, i.inventory_number, i.location, i.responsible_person, i.status])
    return send_file(filepath, as_attachment=True, download_name="orgtexnika.csv")

@app.route("/manager/orgtech/import", methods=["POST"])
@login_required
def manager_orgtech_import():
    if current_user.role != "manager":
        return redirect(url_for("index"))
    file = request.files.get("file")
    if not file:
        flash("Fayl tanlanmadi", "warning")
        return redirect(url_for("manager_orgtech"))
    rows = 0
    for line in file.stream.read().decode("utf-8").splitlines():
        parts = line.split(";")
        if len(parts) < 4 or parts[0] == "id":
            continue
        _, name, inv, loc, resp, status = (parts + ["", "", "", "", "", ""])[:6]
        item = OrgTech(
            name=name.strip(),
            inventory_number=inv.strip(),
            location=loc.strip(),
            responsible_person=resp.strip(),
            status=status.strip() or "active",
        )
        db.session.add(item)
        rows += 1
    if rows:
        db.session.commit()
        flash(f"{rows} ta yozuv import qilindi", "success")
    else:
        flash("Ma'lumot topilmadi", "warning")
    return redirect(url_for("manager_orgtech"))

# --- Employee panel (xodim) ---

@app.route("/employee")
@login_required
def employee_panel():
    if current_user.role != "employee":
        return redirect(url_for("index"))
    my_tasks = Task.query.filter_by(assignee_id=current_user.id).all()
    ijro_tasks = IjroTask.query.filter_by(executor_id=current_user.id).all()
    return render_template("employee/panel.html", tasks=my_tasks, ijro_tasks=ijro_tasks)

@app.route("/employee/task/<int:task_id>/status", methods=["POST"])
@login_required
def employee_update_task_status(task_id):
    if current_user.role != "employee":
        return redirect(url_for("index"))
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get("status")
    if new_status in {"in_progress", "pending", "done", "rejected"}:
        task.status = new_status
        db.session.commit()
        flash("Holat yangilandi", "success")
    return redirect(url_for("employee_panel"))

# --- User panel (talabnoma uchun) ---

@app.route("/user")
@login_required
def user_panel():
    if current_user.role != "user":
        return redirect(url_for("index"))
    my_requests = WarehouseRequest.query.filter_by(creator_id=current_user.id).order_by(WarehouseRequest.created_at.desc()).all()
    return render_template("user/panel.html", requests=my_requests)

@app.route("/user/request/new", methods=["GET", "POST"])
@login_required
def user_new_request():
    if current_user.role != "user":
        return redirect(url_for("index"))
    if request.method == "POST":
        department = request.form.get("department")
        r = WarehouseRequest(creator_id=current_user.id, department=department)
        db.session.add(r)
        db.session.commit()
        names = request.form.getlist("item_name")
        units = request.form.getlist("item_unit")
        amounts = request.form.getlist("item_amount")
        for n, u, a in zip(names, units, amounts):
            if not n.strip():
                continue
            item = WarehouseRequestItem(
                request_id=r.id,
                name=n.strip(),
                unit=u.strip(),
                soralgani=float(a or 0),
            )
            db.session.add(item)
        db.session.commit()
        flash("Talabnoma yuborildi", "success")
        return redirect(url_for("user_panel"))
    products = WarehouseProduct.query.all()
    return render_template("user/new_request.html", products=products)

# --- Run local ---

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_demo_data(db)
    app.run(debug=True)
