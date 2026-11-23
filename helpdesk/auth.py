
from functools import wraps

from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT * FROM users WHERE id = ? AND is_active = 1",
            (user_id,)
        ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if g.user["role"] != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("tickets.dashboard"))

        return view(**kwargs)

    return wrapped_view


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("tickets.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            """
            SELECT * FROM users
            WHERE username = ? AND is_active = 1
            """,
            (username,)
        ).fetchone()

        error = None

        if user is None:
            error = "Incorrect username or password."
        elif not check_password_hash(
            user["password_hash"], password
        ):
            error = "Incorrect username or password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]

            return redirect(url_for("tickets.dashboard"))

        flash(error, "error")

    return render_template("auth/login.html")


@bp.route("/logout", methods=("POST",))
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
