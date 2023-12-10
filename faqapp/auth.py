import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import exc

from faqapp.extensions import db
from faqapp.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


# Decorator for requiring logged-in user
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


# Decorator for requiring user of specific level
def level_required(level):
    def level_decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user.permission_level < level:
                flash("You don't have permission to access this content.")
                return redirect(url_for("faq.index"))

            return view(**kwargs)

        return wrapped_view
    return level_decorator


# Register new user
@bp.route("/register", methods=("GET", "POST"))
def register():
    # Stop logged-in users from spamming register new users
    if g.user is not None:
        return redirect(url_for("faq.index"))
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        # Validate input
        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        # Try to add user to database
        if error is None:
            try:
                user = User(name=username, hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
            except exc.IntegrityError:
                error = f"User {username} is already registered."
            else:
                # Registered successfully, return to login
                return redirect(url_for("auth.login"))

        # Registration error, show user the message so he can try again
        flash(error)

    return render_template("auth/register.html")


# Log in
@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        user = db.session.execute(db.select(User).where(User.name == username)).scalar()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user.hash, password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("faq.index"))

        flash(error)

    return render_template("auth/login.html")


# Log out
@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("faq.index"))


# Check for logged user before requests
@bp.before_app_request
def load_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.execute(db.select(User).where(User.id == user_id)).scalar()
