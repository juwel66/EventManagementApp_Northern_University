import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_

# ---------- Flask App Setup ----------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")   # Change in production

# ---------- Database (SQLite) ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "events.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------- Models ----------
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)  # ISO date string (YYYY-MM-DD)
    desc = db.Column(db.String(500), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(30), nullable=True)

# ---------- Admin Config (simple demo) ----------
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

# ---------- Helpers ----------
@app.context_processor
def inject_globals():
    return {"is_admin": bool(session.get("admin"))}

def require_admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return None

# ---------- Routes ----------
@app.route("/")
def home():
    # Show a few latest events on the homepage
    latest = Event.query.order_by(Event.id.desc()).limit(6).all()
    return render_template("home.html", events=latest)

# Admin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            flash("✅ Logged in as admin", "success")
            return redirect(url_for("admin_dashboard"))
        flash("❌ Invalid credentials", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    # Basic stats
    total_events = Event.query.count()
    total_regs = Registration.query.count()
    # For chart: registrations per event
    events = Event.query.order_by(Event.id).all()
    series = []
    for e in events:
        cnt = Registration.query.filter_by(event_id=e.id).count()
        series.append({"id": e.id, "title": e.title, "date": e.date, "count": cnt, "capacity": e.capacity})
    return render_template("admin_dashboard.html", stats={"events": total_events, "regs": total_regs}, series=series)

# JSON for charts (optional if you prefer fetching)
@app.route("/api/metrics/registrations")
def api_metrics():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    events = Event.query.order_by(Event.id).all()
    data = [{"title": e.title, "date": e.date,
             "count": Registration.query.filter_by(event_id=e.id).count(),
             "capacity": e.capacity} for e in events]
    return jsonify(data)

# Events listing with search & filters
@app.route("/events")
def events():
    q = request.args.get("q", "").strip()
    start = request.args.get("start", "").strip()  # YYYY-MM-DD
    end = request.args.get("end", "").strip()      # YYYY-MM-DD

    query = Event.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Event.title.ilike(like), Event.desc.ilike(like)))

    # Date range filter (string compare works for ISO date strings)
    if start and end:
        query = query.filter(and_(Event.date >= start, Event.date <= end))
    elif start:
        query = query.filter(Event.date >= start)
    elif end:
        query = query.filter(Event.date <= end)

    events = query.order_by(Event.date.asc()).all()
    return render_template("events.html", events=events, q=q, start=start, end=end)

@app.route("/student")
def student_dashboard():
    events = Event.query.order_by(Event.date.asc()).all()
    return render_template("student_dashboard.html", events=events)

# Add event (admin only)
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date = request.form.get("date", "").strip()
        desc = request.form.get("desc", "").strip()
        capacity = int(request.form.get("capacity", "0") or 0)
        if not title or not date or not desc or capacity < 1:
            flash("Please fill all fields correctly.", "warning")
            return redirect(url_for("add_event"))
        ev = Event(title=title, date=date, desc=desc, capacity=capacity)
        db.session.add(ev)
        db.session.commit()
        flash("✅ Event added successfully!", "success")
        return redirect(url_for("events"))
    return render_template("add_event.html")

# Register for an event
@app.route("/register", methods=["GET"])
@app.route("/register/<int:eid>", methods=["GET", "POST"])
def register_event(eid=None):
    if eid is None:
        return redirect(url_for("student_dashboard"))
    event = Event.query.get_or_404(eid)
    count = Registration.query.filter_by(event_id=eid).count()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sid = request.form.get("sid", "").strip()
        mobile = request.form.get("mobile", "").strip()

        # Capacity check
        if count >= event.capacity:
            flash("⚠ Event registration full!", "warning")
            return redirect(url_for("events"))

        # Duplicate check
        exists = Registration.query.filter_by(event_id=eid, student_id=sid).first()
        if exists:
            flash("⚠ Already registered!", "warning")
            return redirect(url_for("events"))

        if not name or not sid or not mobile:
            flash("Please enter your name, student ID and mobile number.", "warning")
            return redirect(url_for("register_event", eid=eid))

        reg = Registration(event_id=eid, student_id=sid, name=name, mobile=mobile)
        db.session.add(reg)
        db.session.commit()
        flash("✅ Registered successfully!", "success")
        return redirect(url_for("events"))

    return render_template("register.html", event=event, count=count)

# Report (admin only)
@app.route("/report")
def report():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    events = Event.query.order_by(Event.id).all()
    rows = []
    for e in events:
        cnt = Registration.query.filter_by(event_id=e.id).count()
        rows.append({"id": e.id, "title": e.title, "date": e.date, "count": cnt, "capacity": e.capacity})
    return render_template("report.html", report=rows)

@app.route("/registrations/<int:eid>")
def view_registrations(eid):
    event = Event.query.get_or_404(eid)
    regs = Registration.query.filter_by(event_id=eid).order_by(Registration.id).all()
    return render_template("registrations.html", event=event, regs=regs)


# ---------- CLI / Init ----------
def init_db():
    with app.app_context():
        db.create_all()
        # ---- Migration: ensure 'mobile' column exists in registration table ----
        try:
            from sqlalchemy import text
            res = db.engine.execute(text("PRAGMA table_info('registration')")).fetchall()
            cols = [r[1] for r in res]
            if 'mobile' not in cols:
                db.engine.execute(text("ALTER TABLE registration ADD COLUMN mobile VARCHAR(30)"))
                print('Added mobile column to registration table')
        except Exception as e:
            print('Migration check failed:', e)

# ---------- Run ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))