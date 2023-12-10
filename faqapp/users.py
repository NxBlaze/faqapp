from flask import abort, Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from faqapp.auth import login_required, level_required
from faqapp.extensions import db
from faqapp.models import User, Note


bp = Blueprint("users", __name__, url_prefix="/users")


# Manage existing users
@bp.route("/manage")
@login_required
@level_required(4)
def manage_users():
    users = db.session.execute(db.select(User).order_by(User.name.asc())).scalars()
    return render_template("users/manage.html", users=users)


@bp.route("<int:id>/edit", methods=("GET", "POST"))
@login_required
@level_required(4)
def edit_user(id):
    user = get_user(id)
    
    if request.method == "POST":
        username = request.form['username']
        permission = request.form['permission_level']
        password = request.form['password']
        error = None

        if not username:
            error = "Username is required."
        if not permission:
            error = "Permission Level is required."

        if error is None:
            user.name = username
            user.permission_level = permission
            if password:
                user.hash=generate_password_hash(password)
            db.session.commit()
            return redirect(url_for("users.manage_users"))
            
        flash(error)

    return render_template("users/edit.html", user=user)


@bp.route("<int:id>/delete", methods=("GET", "POST"))
@login_required
@level_required(4)
def delete_user(id):
    user = get_user(id)
    
    # Stop user from deleting himself
    if user == g.user:
        flash(f"Cannot delete yourself. Please use another admin user if you need to delete user '{user.name}'")
        return redirect(url_for("users.manage_users"))  
    
    admin = db.session.execute(db.select(User).where(User.permission_level == 4).where(User.id != id).order_by(User.id)).scalar()
    
    if request.method == "POST":
        error = None
        
        
        if error is None:
            keep_notes = request.form['delete']
            if not keep_notes:
                error = "Please choose what to do with existing notes."
            if keep_notes not in ["keep", "delete"]:
                error = f"Unknown command {keep_notes}"


        if error is None:
            notes = db.session.execute(db.select(Note).where(Note.author_id == user.id)).scalars()
            if notes is not None:
                for note in notes:
                    note.author_id = admin.id
                    db.session.commit()
                    
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for("users.manage_users"))
    
        flash(error)

    return render_template("users/delete.html", user=user, admin=admin)


# Get user by ID
def get_user(id):
    user = db.session.execute(db.select(User).where(User.id == id)).scalar()

    if user is None:
        abort(404, "User doesn't exist.")

    if g.user.permission_level < 4:
        abort(403)

    return user