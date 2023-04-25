import functools
import os
import random
import string
from collections import defaultdict
import sqlite3
from typing import Tuple

from flask import Flask, session, render_template, request, redirect

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "A_Not_So_Secret_key")
app.data = defaultdict(lambda: {"flags": [], "used_hints": False})
app.total_flags = 1
# TODO Implement a leaderboard for the first to find each flag
# TODO Flag ideas
#      - Cookie based flag that users modify for a request
#      - Change a request header?
#      - Login form with weak creds such as admin admin
#      - Login form with creds in HTML


def get_db_connection():
    return sqlite3.connect("db/db.db")


def get_user(session_id: str) -> Tuple[str, str, int]:
    con = get_db_connection()
    cursor = con.cursor()
    res = cursor.execute("""SELECT * FROM User WHERE session_id = ?""", (session_id,))
    try:
        data = res.fetchone()
    except TypeError:
        # Doesn't exist for some reason
        flags = ""
        cursor.execute("""INSERT INTO User VALUES (?, ?, ?)""", (session_id, flags, 0))
        con.commit()
        data = (session_id, "", 0)
    else:
        if data is None:
            flags = ""
            cursor.execute(
                """INSERT INTO User VALUES (?, ?, ?)""", (session_id, flags, 0)
            )
            con.commit()
            data = (session_id, "", 0)
    finally:
        cursor.close()
        con.close()
        return data  # noqa


initial_con = get_db_connection()
cur = initial_con.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS User(session_id TEXT PRIMARY KEY, flags TEXT NOT NULL, used_hints INTEGER)"
)
cur.close()
initial_con.commit()
initial_con.close()


def register_flag_found(session_id: str, flag: str):
    con = get_db_connection()
    cursor = con.cursor()
    _, data, _ = get_user(session_id)

    if flag not in data:
        data += f",{flag}"
        cursor.execute(
            """UPDATE User SET flags = ? WHERE session_id = ?""",
            (flag, session_id),
        )
        con.commit()
    cursor.close()
    con.close()
    return redirect("/?flag_found=true")


def require_session():
    def middle(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if not session.get("id"):
                return redirect(f"/session?redirect_to={request.path}")

            return func(*args, **kwargs)

        return inner

    return middle


@app.route("/")
@require_session()
def index():
    flag_found = request.args.get("flag_found", "false").lower() == "true"

    _, flags, used_hints = get_user(session["id"])
    return render_template(
        "index.html",
        flag_found=flag_found,
        session_id=session["id"],
        total_flags=app.total_flags,
        user_flags=[f for f in flags.split(",") if bool(f)],
        has_used_hints=bool(used_hints),
    )


@app.route("/session", methods=["GET", "POST"])
def get_session():
    redirect_url = request.args.get("redirect_to", "/")
    if request.method != "POST":
        return render_template("session.html", redirect=redirect_url)

    if not session.get("id"):
        session_id = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        session["id"] = session_id

        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("""INSERT INTO User VALUES (?, ?, ?)""", (session_id, "", 0))
        con.commit()
        cursor.close()
        con.close()

    if redirect_url not in {"/"}:
        return register_flag_found(session["id"], "session_flag")

    return redirect("/")


@app.route("/session/clear", methods=["GET", "POST"])
@require_session()
def clear_session():
    if request.method != "POST":
        return render_template("you_sure.html")

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("""DELETE FROM User WHERE session_id = ?""", (session["id"],))
    con.commit()
    cursor.close()
    con.close()
    session.clear()

    return redirect("/")


@app.route("/hints", methods=["GET", "POST"])
@require_session()
def see_hints():
    if request.method != "POST":
        return render_template("you_sure.html")

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute(
        """UPDATE User SET used_hints = 1 WHERE session_id = ?""",
        (session["id"],),
    )
    con.commit()
    cursor.close()
    con.close()
    app.data[session["id"]]["used_hints"] = True
    return render_template("hints.html")


@app.route("/login")
@require_session()
def login():
    return render_template("login.html")


@app.route("/dash", methods=["GET", "POST"])
def dashboard():
    if request.method != "POST":
        return render_template("dash_form.html")

    phrase = request.form["phrase"]
    if phrase != os.environ.get("DASH_PHRASE"):
        return render_template("dash_form.html")

    con = get_db_connection()
    cursor = con.cursor()
    res = cursor.execute("""SELECT * FROM User""")
    data = res.fetchall()
    cursor.close()
    con.close()
    return render_template("dash.html", data=data)


if __name__ == "__main__":
    app.run()
