from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"  # o'zing o'zgartir

# ==========================
# DATABASE SETTINGS
# ==========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(BASE_DIR, "data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==========================
# LOGIN MANAGER
# ==========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ==========================
# USER MODEL
# ==========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # "user" yoki "admin"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================
# DATABASE CREATE
# ==========================
with app.app_context():
    db.create_all()


# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    return render_template("home.html")  # Agar html bo'lmasa oddiy text qaytarsin:
    # return "Welcome!"


# ------------ REGISTER ------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Bu username band!", "danger")
            return redirect("/register")

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, role="user")
        db.session.add(user)
        db.session.commit()

        flash("Muvaffaqiyatli ro‘yxatdan o‘tildi!", "success")
        return redirect("/login")

    return render_template("register.html")


# ------------ LOGIN ------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Noto‘g‘ri login yoki parol!", "danger")
            return redirect("/login")

        login_user(user)
        return redirect("/dashboard")

    return render_template("login.html")


# ------------ LOGOUT ------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# ------------ USER DASHBOARD ------------
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Salom, {current_user.username}!"


# ------------ ADMIN PANEL ------------
@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        return "Ruxsat yo‘q! (Admin kerak)"

    users = User.query.all()
    return render_template("admin.html", users=users)


# ------------ HEALTHCHECK (Koyeb uchun shart) ------------
@app.route("/health")
def health():
    return "OK", 200


# =============== RUN ===============
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
