from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================
# MODELS
# =====================



class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 👇 ADD THESE

    student_profile = db.relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False
    )

    company_profile = db.relationship(
        "CompanyProfile",
        back_populates="user",
        uselist=False
    )
    
# StudentProfile model
class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)
    skills = db.Column(db.String(200))
    resume = db.Column(db.String(200))
    placement_status = db.Column(db.String(50), default="Not Placed")

    # relation to User
    user = db.relationship("User", back_populates="student_profile")

    # 🔥 ADD THIS (very important)
    applications = db.relationship(
        "Application",
        back_populates="student"
    )




  
#CompanyProfile model
class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    # foriegn key one to one each CompanyProfile belongs to one User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    company_name = db.Column(db.String(150))
    industry = db.Column(db.String(100))
    website = db.Column(db.String(150))
    location = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    # one to one each CompanyProfile belongs to one User
    user = db.relationship("User", back_populates="company_profile")
    #one to many relationship one company can post many jobs
    jobs = db.relationship(
        "Job",
        back_populates="company"
    )
#job model
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    # foriegn key many to one many jobs posted by 1 company
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company_profiles.id")
    )
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    skills = db.Column(db.String(200))
    salary = db.Column(db.String(50))
    job_type = db.Column(db.String(50), default="Full-time")
    is_approved = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    # many jobs posted by 1 company
    company = db.relationship("CompanyProfile", back_populates="jobs")
    #one to many one Job can have many Applications
    applications = db.relationship(
        "Application",
        back_populates="job"
    )
#application model
class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    # many to one many applications sent for one job
    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id")
    )
    # many to one many applications sent by one student
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id")
    )
    status = db.Column(db.String(50), default="Applied")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    remarks = db.Column(db.String(200))
    # many to one many applications sent for one job
    job = db.relationship("Job", back_populates="applications")
    # many to one many applications sent by one student
    student = db.relationship("StudentProfile", back_populates="applications")

# =====================
# APP START
# =====================


@app.route('/')
def index():
    return render_template('index.html')







@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]  # student / company

        # block admin registration
        if role == "admin":
            return "Admin cannot be registered"

        if User.query.filter_by(email=email).first():
            return "Email already registered"

        user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            is_approved=False if role == "company" else True
        )

        db.session.add(user)
        db.session.commit()
    return render_template("register.html")





@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if not user:
            print('186 line ')
            return "No user found"

        
        if user.password != password:
            print(user.password, password)
            return "Wrong password"

        if user.role == "company" and not user.is_approved:
            return "u are not approved"

    

        if user.role == "Admin":
            return redirect('admin_dashboard')

        elif user.role == "company":
            return redirect('company_dashboard')

        elif user.role == "student":
            return redirect('student_dashboard')

    return render_template("login.html")


@app.route("/company_dashboard")
def company_dashboard():
    return "thsi is companyd ashboar"

@app.route("/student_dashboard")
def student_dashboard():
    return "thsi is student_dashboard ashboar"

@app.route("/admin_dashboard")
def admin_dashboard():
    return "thsi is admin_dashboard ashboar"
    
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

        user = User.query.filter_by(name='admin')
        if not user:
            admin_user = User(
                name="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin"),
                role="admin",
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
