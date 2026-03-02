from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "mysecret123"
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
    is_closed = db.Column(db.Boolean, default=False)
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

@app.route("/company-details/<int:company_id>")
def company_details(company_id):

    # get company profile
    company = CompanyProfile.query.filter_by(id=company_id).first()

    if not company:
        return "Company not found", 404

    return render_template(
        "company_details.html",
        company=company
    )
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post-job',methods=['GET','POST'])
def job_post():
    if request.method == 'POST':
        if "user_id" not in session:
            return redirect("/login")

        company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

        if not company:
            return "Please complete company profile first"

        if request.method == "POST":
            job = Job(
                company_id=company.id,
                title=request.form["title"],
                skills=request.form["skills"],
                salary=request.form["salary"],

            )

            db.session.add(job)
            db.session.commit()

        return redirect("/company_dashboard")

    return render_template('job_post.html')






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
        

        session['user_id'] = user.id
        session['role'] = user.role

        if user.role == "company" and not user.is_approved:
            return "u are not approved"

    

        if user.role == "admin":
            return redirect('admin_dashboard')

        elif user.role == "company":
            return redirect('company_dashboard')

        elif user.role == "student":
            return redirect('student_dashboard')

    return render_template("login.html")



@app.route("/company_dashboard")
def company_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return redirect("/complete-company-profile")

    jobs = Job.query.filter_by(company_id=company.id).all()

    job_data = []
    all_shortlisted = []   # ⭐ NEW LIST

    for job in jobs:
        total_apps = Application.query.filter_by(job_id=job.id).count()

        shortlisted = Application.query.filter_by(
            job_id=job.id,
            status="Shortlisted"
        ).all()

        all_shortlisted.extend(shortlisted)  # ⭐ collect all

        job_data.append({
            "job": job,
            "total_apps": total_apps
        })

    return render_template(
        "company_dashboard.html",
        company=company,
        jobs=job_data,
        shortlisted=all_shortlisted   # ⭐ PASS GLOBAL LIST
    )

@app.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company profile not found", 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        return "Job not found", 404

    # 🔥 Check if applications exist
    application_count = Application.query.filter_by(job_id=job.id).count()

    if application_count > 0:
        return render_template(
            "delete_warning.html",
            job=job,
            application_count=application_count
        )

    # If no applications → delete directly
    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")



@app.route("/confirm-delete/<int:job_id>", methods=["POST"])
def confirm_delete(job_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company not found", 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        return "Job not found", 404

    # delete related applications first
    Application.query.filter_by(job_id=job.id).delete()

    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")



@app.route("/complete-company-profile", methods=["GET", "POST"])
def complete_company_profile():

    if not session.get('user_id'):
        return redirect('login')

    user_id = session['user_id']
    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":

        # ✅ CASE 1: Profile exists → UPDATE


        if company:
            print('thise is update ')
            company.company_name = request.form["company_name"]
            company.industry = request.form["industry"]
            company.website = request.form["website"]
            company.location = request.form["location"]
            company.company_size = request.form["company_size"]

            db.session.commit()
            return redirect("/company_dashboard")
        else:
            print('thsi si insert')
            company = CompanyProfile(
                user_id=user_id,
                company_name=request.form["company_name"],
                industry=request.form["industry"],
                website=request.form["website"],
                location=request.form["location"],
                company_size=request.form["company_size"],
            )   
            db.session.add(company)

            db.session.commit()

            return redirect("/company_dashboard")
    return render_template("complete_company_profile.html")

@app.route("/job-applications/<int:job_id>")
def view_applications(job_id):
    applications = Application.query.filter_by(job_id=job_id).all()

    return render_template(
        "applications.html",
        applications=applications
    )

@app.route("/company/student/<int:student_id>")
def view_student_profile(student_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company profile not found", 404

    student = StudentProfile.query.filter_by(id=student_id).first()
    if not student:
        return "Student not found", 404

    # using relationship instead of join
    applications = [
        app for app in student.applications
        if app.job.company_id == company.id
    ]

    total_applied = len(applications)

    return render_template(
        "student_detail.html",
        student=student,
        applications=applications,
        total_applied=total_applied
    )

    
@app.route("/toggle-status/<int:app_id>/<string:action>")
def toggle_status(app_id, action):
    if "user_id" not in session:
        return redirect("/login")

    application = Application.query.get_or_404(app_id)

    if action == "shortlist":
        if application.status == "Shortlisted":
            application.status = "Applied"   # unshortlist
        else:
            application.status = "Shortlisted"

    elif action == "select":
        if application.status == "Selected":
            application.status = "Shortlisted"   # unselect
        else:
            application.status = "Selected"

    elif action == "reject":
        if application.status == "Rejected":
            application.status = "Applied"   # unreject
        else:
            application.status = "Rejected"

    db.session.commit()

    return redirect(request.referrer)

###########################

@app.route("/student_dashboard")
def student_dashboard():

    # check login
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # get student profile
    student = StudentProfile.query.filter_by(user_id=user_id).first()

    # get search value from URL
    search = request.args.get("search")

    # base query (only approved & open jobs)
    jobs_query = Job.query.filter_by(is_approved=True, is_closed=False)

    # if search exists -> filter
    if search:
        jobs_query = jobs_query.join(CompanyProfile).filter(
            (CompanyProfile.company_name.ilike(f"%{search}%")) |
            (Job.title.ilike(f"%{search}%")) |
            (Job.skills.ilike(f"%{search}%"))
        )

    jobs = jobs_query.all()

    # store applied jobs
    applied_jobs = {}

    if student:
        for app in student.applications:
            applied_jobs[app.job_id] = app.status

    return render_template(
        "student_dashboard.html",
        student=student,
        jobs=jobs,
        applied_jobs=applied_jobs
    )

@app.route("/apply-job/<int:job_id>")
def apply_job(job_id):
    if "user_id" not in session:
        return redirect("/login")

    student = StudentProfile.query.filter_by(
        user_id=session["user_id"]).first()

    if not student:
        return "Complete profile first!"

    # Check duplicate apply
    existing = Application.query.filter_by(
        job_id=job_id,
        student_id=student.id
    ).first()

    if existing:
        return "Already applied!"

    app = Application(
        job_id=job_id,
        student_id=student.id
    )

    db.session.add(app)
    db.session.commit()

    return redirect("/student_dashboard")


@app.route("/complete-student-profile", methods=["GET", "POST"])
def complete_student_profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":

        if not student:
            student = StudentProfile(user_id=user_id)
            db.session.add(student)

        student.department = request.form["department"]
        student.cgpa = request.form["cgpa"]
        student.resume = request.form["resume"]

        db.session.commit()

        return redirect("/student_dashboard")

    return render_template("complete_student_profile.html", student=student)


#####################
# admin dashboard 
#####################
@app.route("/admin_dashboard")
def admin_dashboard():

    total_students = User.query.filter_by(role="student").count()
    total_companies = User.query.filter_by(role="company").count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    pending_companies = User.query.filter_by(role="company", is_approved=False).all()
    pending_jobs = Job.query.filter_by(is_approved=False).all()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        pending_companies=pending_companies,
        pending_jobs=pending_jobs
    )

@app.route("/admin/company/<int:user_id>/approve")
def approve_company(user_id):

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    return redirect("/admin_dashboard")


@app.route("/admin/company/<int:user_id>/reject")
def reject_company(user_id):

    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()

    return redirect("/admin/dashboard")

@app.route("/admin/job/<int:job_id>/approve")
def approve_job(job_id):

    job = Job.query.get_or_404(job_id)
    job.is_approved = True
    db.session.commit()

    return redirect("/admin/dashboard")


@app.route("/admin/job/<int:job_id>/reject")
def reject_job(job_id):

    job = Job.query.get_or_404(job_id)
    job.is_closed = True
    db.session.commit()

    return redirect("/admin/dashboard")




@app.route("/admin/students")
def view_students():

    search = request.args.get("search")

    query = User.query.filter_by(role="student")

    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    students = query.all()

    return render_template("admin_students.html", students=students)







@app.route("/admin/companies")
def view_companies():

    search = request.args.get("search")

    query = CompanyProfile.query

    if search:
        query = query.filter(
            (CompanyProfile.company_name.ilike(f"%{search}%")) |
            (CompanyProfile.industry.ilike(f"%{search}%"))
        )

    companies = query.all()

    return render_template("admin_companies.html", companies=companies)

@app.route("/admin/user/<int:user_id>/toggle")
def toggle_user(user_id):

    user = User.query.get_or_404(user_id)

    # switch active status
    user.is_active = not user.is_active

    db.session.commit()

    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('login')


if __name__ == "__main__":

    with app.app_context():
        db.create_all()
     
        user = User.query.filter_by(name='admin').first()
        if not user:
            print('shubham')
            admin_user = User(
                name="admin",
                email="admin@gmail.com",
                password="admin",
                role="admin",
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
