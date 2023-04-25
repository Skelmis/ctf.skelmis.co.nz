import functools
import os
import random
import string
from collections import defaultdict

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


def register_flag_found(session_id: str, flag: str):
    app.data[session_id]["flags"].append(flag)
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

    return render_template(
        "index.html",
        flag_found=flag_found,
        session_id=session["id"],
        total_flags=app.total_flags,
        user_flags=app.data[session["id"]]["flags"],
        has_used_hints=app.data[session["id"]]["used_hints"],
    )


@app.route("/session", methods=["GET", "POST"])
def get_session():
    redirect_url = request.args.get("redirect_to", "/")
    if request.method != "POST":
        return render_template("session.html", redirect=redirect_url)

    if redirect_url not in {"/"}:
        return register_flag_found(session["id"], "session_flag")

    if not session.get("id"):
        session["id"] = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )

    return redirect("/")


@app.route("/session/clear", methods=["GET", "POST"])
@require_session()
def clear_session():
    if request.method != "POST":
        return render_template("you_sure.html")

    session.clear()
    return redirect("/")


@app.route("/hints", methods=["GET", "POST"])
@require_session()
def see_hints():
    if request.method != "POST":
        return render_template("you_sure.html")

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

    return render_template("dash.html", data=app.data)


if __name__ == "__main__":
    app.run()
