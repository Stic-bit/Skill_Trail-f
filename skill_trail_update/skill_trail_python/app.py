
import os
import sqlite3
import secrets
import hashlib
import json
from functools import wraps
from datetime import datetime, timezone

from flask import (
    Flask,
    g,
    jsonify,
    request,
    session,
    render_template,
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get("SKILL_TRAIL_DB") or (
    "/tmp/skill_trail.db"
    if os.environ.get("VERCEL")
    else os.path.join(APP_DIR, "skill_trail.db")
)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SKILL_TRAIL_SECRET",
    secrets.token_hex(32),
)

ADMIN_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "").split(",")
    if e.strip()
}

MAX_STATE_BYTES = 900_000

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
)


# --------------------------------------------------
# TOPICS AND COURSES
# --------------------------------------------------

TOPICS = [
    {"id": "python", "label": "Python", "group": "Computing"},
    {"id": "web", "label": "Web development", "group": "Computing"},
    {"id": "data", "label": "Data science", "group": "Computing"},
    {"id": "ml", "label": "Machine learning", "group": "Computing"},
    {
        "id": "embedded",
        "label": "Embedded systems",
        "group": "Electronics & hardware",
    },
    {
        "id": "instr",
        "label": "Instrumentation & sensors",
        "group": "Electronics & hardware",
    },
    {
        "id": "dsp",
        "label": "Signal processing",
        "group": "Electronics & hardware",
    },
    {
        "id": "nuclear",
        "label": "Nuclear physics",
        "group": "Physics & nuclear",
    },
    {
        "id": "radiation",
        "label": "Radiation detection",
        "group": "Physics & nuclear",
    },
    {
        "id": "quantum",
        "label": "Quantum mechanics",
        "group": "Physics & nuclear",
    },
    {
        "id": "research",
        "label": "Research methods",
        "group": "Career & skills",
    },
    {
        "id": "prob",
        "label": "Probability & statistics",
        "group": "Mathematics",
    },
]

COURSES = [
    {
        "id": "c-python",
        "topic": "python",
        "title": "Python Foundations",
        "kind": "Course",
        "level": "Beginner",
        "hours": 6,
        "description": (
            "Variables, functions, collections, files "
            "and practical problem-solving."
        ),
    },
    {
        "id": "c-data",
        "topic": "data",
        "title": "Data Analysis with Python",
        "kind": "Project path",
        "level": "Beginner",
        "hours": 8,
        "description": (
            "Use CSV files, pandas-style workflows and "
            "charts to explore data."
        ),
    },
    {
        "id": "c-embedded",
        "topic": "embedded",
        "title": "Embedded Systems Primer",
        "kind": "Course",
        "level": "Intermediate",
        "hours": 10,
        "description": (
            "Microcontrollers, inputs, outputs, timers "
            "and serial communication."
        ),
    },
    {
        "id": "c-instr",
        "topic": "instr",
        "title": "Sensors and Measurement",
        "kind": "Course",
        "level": "Intermediate",
        "hours": 6,
        "description": (
            "Measurement concepts, sensor calibration "
            "and signal conditioning."
        ),
    },
    {
        "id": "c-nuclear",
        "topic": "nuclear",
        "title": "Nuclear Structure and Decay",
        "kind": "Reading path",
        "level": "Beginner",
        "hours": 10,
        "description": (
            "Binding energy, half-life and decay chains "
            "using safe simulations."
        ),
    },
    {
        "id": "c-rad",
        "topic": "radiation",
        "title": "Radiation Counting Statistics",
        "kind": "Reading path",
        "level": "Intermediate",
        "hours": 5,
        "description": (
            "Explore counting uncertainty with synthetic "
            "data and simulations."
        ),
    },
    {
        "id": "c-dsp",
        "topic": "dsp",
        "title": "Sampling and the FFT",
        "kind": "Course",
        "level": "Intermediate",
        "hours": 5,
        "description": (
            "Sampling, aliasing and frequency-domain analysis."
        ),
    },
    {
        "id": "c-research",
        "topic": "research",
        "title": "Research Skills Starter",
        "kind": "Guide",
        "level": "Beginner",
        "hours": 3,
        "description": (
            "Research questions, source evaluation, "
            "notebooks and reproducibility."
        ),
    },
]


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            DB_PATH,
            timeout=10,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db_dir = os.path.dirname(DB_PATH) or "."
    os.makedirs(db_dir, exist_ok=True)

    db = sqlite3.connect(DB_PATH, timeout=10)

    try:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS preferences (
                user_id INTEGER PRIMARY KEY
                    REFERENCES users(id) ON DELETE CASCADE,
                interests TEXT NOT NULL DEFAULT '[]',
                goal TEXT NOT NULL DEFAULT 'Build practical skills',
                level TEXT NOT NULL DEFAULT 'Beginner',
                hours_per_week INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS user_state (
                user_id INTEGER PRIMARY KEY
                    REFERENCES users(id) ON DELETE CASCADE,
                data TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER NOT NULL
                    REFERENCES users(id) ON DELETE CASCADE,
                course_id TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, course_id)
            );

            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL
                    REFERENCES users(id) ON DELETE CASCADE,
                course_id TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                issued_at TEXT NOT NULL
            );
            """
        )

        db.commit()
    finally:
        db.close()


# --------------------------------------------------
# PASSWORDS AND AUTHENTICATION
# --------------------------------------------------

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        260000,
    ).hex()

    return f"{salt}${digest}"


def check_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)

        calculated_digest = password_hash(
            password,
            salt,
        ).split("$", 1)[1]

        return secrets.compare_digest(
            calculated_digest,
            digest,
        )
    except (ValueError, AttributeError):
        return False


def user_row(user_id=None):
    if user_id is None:
        user_id = session.get("user_id")

    if not user_id:
        return None

    return get_db().execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not user_row():
            return jsonify(
                error="Please sign in to continue."
            ), 401

        return fn(*args, **kwargs)

    return wrapper


def json_body():
    return request.get_json(silent=True) or {}


def is_admin_email(email):
    return (email or "").lower() in ADMIN_EMAILS


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        row = user_row()

        if not row:
            return jsonify(
                error="Please sign in to continue."
            ), 401

        if not is_admin_email(row["email"]):
            return jsonify(error="Admin access only."), 403

        return fn(*args, **kwargs)

    return wrapper


def load_state(user_id):
    row = get_db().execute(
        "SELECT data FROM user_state WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if not row:
        return {}

    try:
        data = json.loads(row["data"])
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# HEALTH CHECK WITH SQLITE CONNECTION TEST
# --------------------------------------------------

@app.get("/api/health")
def health():
    db_dir = os.path.dirname(DB_PATH) or "."

    result = {
        "status": "ok",
        "service": "Skill Trail API",
        "language": "Python",
        "database": "SQLite",
        "vercel_env": bool(os.environ.get("VERCEL")),
        "db_path": DB_PATH,
        "db_parent_exists": os.path.isdir(db_dir),
        "db_parent_writable": os.access(db_dir, os.W_OK),
    }

    try:
        with sqlite3.connect(
            DB_PATH,
            timeout=5,
        ) as db:
            db.execute("SELECT 1")

        result["database_connection"] = "ok"

    except sqlite3.Error as exc:
        result["database_connection"] = "failed"
        result["database_error"] = str(exc)

    return jsonify(result)


# --------------------------------------------------
# TOPICS AND COURSES
# --------------------------------------------------

@app.get("/api/topics")
def topics():
    return jsonify(topics=TOPICS)


@app.get("/api/courses")
def courses():
    topic = request.args.get("topic")

    rows = [
        course
        for course in COURSES
        if not topic or course["topic"] == topic
    ]

    return jsonify(courses=rows)


# --------------------------------------------------
# REGISTRATION
# --------------------------------------------------

@app.post("/api/register")
def register():
    data = json_body()

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if len(name) < 2:
        return jsonify(
            error="Please enter your name."
        ), 400

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify(
            error="Enter a valid email address."
        ), 400

    if len(password) < 8:
        return jsonify(
            error="Use a password with at least 8 characters."
        ), 400

    db = get_db()

    try:
        cur = db.execute(
            """
            INSERT INTO users (
                name, email, password_hash, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password_hash(password),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        uid = cur.lastrowid

        db.execute(
            "INSERT INTO preferences(user_id) VALUES(?)",
            (uid,),
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        return jsonify(
            error=(
                "An account with that email already exists. "
                "Try signing in."
            )
        ), 409

    session.clear()
    session["user_id"] = uid

    return jsonify(
        user={
            "id": uid,
            "name": name,
            "email": email,
        }
    ), 201


# --------------------------------------------------
# LOGIN AND LOGOUT
# --------------------------------------------------

@app.post("/api/login")
def login():
    data = json_body()

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    row = get_db().execute(
        """
        SELECT id, name, email, password_hash
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    if not row or not check_password(
        password,
        row["password_hash"],
    ):
        return jsonify(
            error="Email or password is incorrect."
        ), 401

    session.clear()
    session["user_id"] = row["id"]

    return jsonify(
        user={
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
        }
    )


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


# --------------------------------------------------
# CURRENT USER, PREFERENCES, PROGRESS AND CERTIFICATES
# --------------------------------------------------

@app.get("/api/me")
def me():
    row = user_row()

    if not row:
        return jsonify(user=None)

    db = get_db()

    pref = db.execute(
        """
        SELECT interests, goal, level, hours_per_week
        FROM preferences
        WHERE user_id = ?
        """,
        (row["id"],),
    ).fetchone()

    if pref is None:
        return jsonify(
            error="User preferences were not found."
        ), 500

    progress = db.execute(
        """
        SELECT course_id, completed
        FROM progress
        WHERE user_id = ?
        """,
        (row["id"],),
    ).fetchall()

    certs = db.execute(
        """
        SELECT course_id, code, issued_at
        FROM certificates
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (row["id"],),
    ).fetchall()

    return jsonify(
        user={
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "is_admin": is_admin_email(row["email"]),
        },
        state=load_state(row["id"]),
        preferences={
            "interests": json.loads(pref["interests"]),
            "goal": pref["goal"],
            "level": pref["level"],
            "hours_per_week": pref["hours_per_week"],
        },
        progress=[
            {
                "course_id": item["course_id"],
                "completed": bool(item["completed"]),
            }
            for item in progress
        ],
        certificates=[
            {
                "course_id": item["course_id"],
                "code": item["code"],
                "issued_at": item["issued_at"],
            }
            for item in certs
        ],
    )


@app.put("/api/preferences")
@require_auth
def update_preferences():
    data = json_body()
    interests = data.get("interests", [])

    if not isinstance(interests, list):
        return jsonify(
            error="Interests must be a list."
        ), 400

    valid = {topic["id"] for topic in TOPICS}

    interests = [
        item
        for item in dict.fromkeys(interests)
        if isinstance(item, str) and item in valid
    ]

    goal = str(
        data.get("goal", "Build practical skills")
    )[:120]

    level = data.get("level", "Beginner")

    if level not in (
        "Beginner",
        "Intermediate",
        "Advanced",
    ):
        return jsonify(
            error="Choose a valid learning level."
        ), 400

    try:
        hours = max(
            1,
            min(30, int(data.get("hours_per_week", 5))),
        )
    except (TypeError, ValueError):
        hours = 5

    db = get_db()

    db.execute(
        """
        UPDATE preferences
        SET interests = ?, goal = ?, level = ?,
            hours_per_week = ?
        WHERE user_id = ?
        """,
        (
            json.dumps(interests),
            goal,
            level,
            hours,
            session["user_id"],
        ),
    )

    db.commit()

    return jsonify(ok=True)


@app.put("/api/progress/<course_id>")
@require_auth
def update_progress(course_id):
    valid_course_ids = {
        course["id"] for course in COURSES
    }

    if course_id not in valid_course_ids:
        return jsonify(
            error="Course not found."
        ), 404

    completed = bool(
        json_body().get("completed", True)
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO progress (
            user_id, course_id, completed, updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, course_id)
        DO UPDATE SET
            completed = excluded.completed,
            updated_at = excluded.updated_at
        """,
        (
            session["user_id"],
            course_id,
            int(completed),
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    if completed:
        exists = db.execute(
            """
            SELECT id
            FROM certificates
            WHERE user_id = ? AND course_id = ?
            """,
            (session["user_id"], course_id),
        ).fetchone()

        if not exists:
            db.execute(
                """
                INSERT INTO certificates (
                    user_id, course_id, code, issued_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    course_id,
                    "ST-" + secrets.token_hex(5).upper(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    db.commit()

    return jsonify(
        ok=True,
        completed=completed,
    )


@app.get("/api/certificates")
@require_auth
def certificates():
    rows = get_db().execute(
        """
        SELECT course_id, code, issued_at
        FROM certificates
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],),
    ).fetchall()

    return jsonify(
        certificates=[
            {
                "course_id": row["course_id"],
                "code": row["code"],
                "issued_at": row["issued_at"],
            }
            for row in rows
        ]
    )


# --------------------------------------------------
# PER-USER APP STATE (profile, interests, settings, saved items...)
# --------------------------------------------------

@app.get("/api/state")
@require_auth
def get_state():
    return jsonify(state=load_state(session["user_id"]))


@app.put("/api/state")
@require_auth
def put_state():
    state = json_body().get("state")

    if not isinstance(state, dict):
        return jsonify(error="State must be an object."), 400

    # Never trust privilege or credential fields sent by the browser.
    for blocked in ("hash", "isAdmin", "_remote", "role_admin"):
        state.pop(blocked, None)

    raw = json.dumps(state)

    if len(raw.encode()) > MAX_STATE_BYTES:
        return jsonify(error="Saved data is too large."), 413

    db = get_db()

    db.execute(
        """
        INSERT INTO user_state (user_id, data, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            data = excluded.data,
            updated_at = excluded.updated_at
        """,
        (
            session["user_id"],
            raw,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    name = str(state.get("name", "")).strip()

    if len(name) >= 2:
        db.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name[:80], session["user_id"]),
        )

    db.commit()

    return jsonify(ok=True)


@app.delete("/api/account")
@require_auth
def delete_account():
    db = get_db()

    db.execute(
        "DELETE FROM users WHERE id = ?",
        (session["user_id"],),
    )

    db.commit()
    session.clear()

    return jsonify(ok=True)


# --------------------------------------------------
# ADMIN (checked on the server)
# --------------------------------------------------

@app.get("/api/admin/users")
@require_admin
def admin_users():
    rows = get_db().execute(
        """
        SELECT id, name, email, created_at
        FROM users
        ORDER BY id DESC
        LIMIT 500
        """
    ).fetchall()

    return jsonify(
        users=[
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "created_at": row["created_at"],
                "state": load_state(row["id"]),
            }
            for row in rows
        ]
    )


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

init_db()


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )
