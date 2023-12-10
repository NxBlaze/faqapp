from flask import (
    abort,
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from datetime import datetime, timezone

from faqapp.extensions import db
from faqapp.models import Note, User, Category
from faqapp.auth import login_required, level_required

bp = Blueprint("faq", __name__)


# Homepage
@bp.route("/")
@login_required
def index():
    categories = build_category_tree(load_categories())

    faqs = (
        db.session.execute(
            db.select(Note).join(User).join(Category).order_by(Note.create_date)
        )
        .scalars()
        .all()
    )

    return render_template("faq/index.html", faqs=faqs, categories=categories)


# Display notes by category
@bp.route("/cat/<int:id>")
@login_required
def notes_by_category(id):
    categories = build_category_tree(load_categories())

    faqs = (
        db.session.execute(
            db.select(Note)
            .join(User)
            .join(Category)
            .order_by(Note.create_date)
            .where(Note.category == id)
        )
        .scalars()
        .all()
    )

    return render_template("faq/index.html", faqs=faqs, categories=categories)


# Add new note
@bp.route("/add", methods=("GET", "POST"))
@login_required
@level_required(2)
def add_note():
    if request.method == "POST":
        note_title = request.form["title"]
        note_content = request.form["note_content"]
        cat = request.form["cat_selection"]
        error = None

        if not note_title:
            error = "Title is required."
        if not cat:
            error = "Category is required."

        if error is not None:
            flash(error)
        else:
            note = Note(
                title=note_title,
                category=cat,
                content=note_content,
                author_id=g.user.id,
            )
            db.session.add(note)
            db.session.commit()
            return redirect(url_for("faq.index"))

    categories = build_category_tree(load_categories())
    return render_template("faq/add.html", categories=categories)


# Update note
@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
@level_required(2)
def update_note(id):
    note = get_note(id)

    if request.method == "POST":
        note_title = request.form["title"]
        note_content = request.form["note_content"]
        cat = request.form["cat_selection"]
        error = None

        if not note_title:
            error = "Title is required."
        if not cat:
            error = "Category is required."
        if error is not None:
            flash(error)
        else:
            note.title = note_title
            note.content = note_content
            note.category = cat
            note.update_date = datetime.now()
            db.session.commit()
            return redirect(url_for("faq.index"))

    categories = build_category_tree(load_categories())
    return render_template("faq/update.html", note=note, categories=categories)


# Delete note
@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
@level_required(2)
def delete_note(id):
    note = get_note(id)

    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("faq.index"))


# Category management
@bp.route("/cat/manage")
@login_required
@level_required(3)
def manage_categories():
    categories = load_categories()

    return render_template("category/manage.html", categories=categories)


# Add new category
@bp.route("/cat/add", methods=("GET", "POST"))
@login_required
@level_required(3)
def add_category():
    if request.method == "POST":
        new_category_name = request.form["name"]
        new_category_parent = request.form["cat_selection"]
        error = None

        # Validate input
        if not new_category_name:
            error = "Category name is required."
        if not new_category_parent:
            error = "Please select one of the options."

        # Check whether category under that name is already in db
        category_in_db = db.session.execute(
            db.select(Category.id).where(Category.name == new_category_name)
        ).scalar()
        if category_in_db is not None:
            error = f"Category named '{new_category_name}' already exists."

        if error is None:
            # If no parent, find the highest tree index of top level categories
            # As base for tree attribute for new category
            if new_category_parent == "0":
                current_tree = db.session.execute(
                    db.select(Category.tree)
                    .where(Category.level == 0)
                    .order_by(Category.tree.desc())
                ).scalar()

                # Set the tree attribute of new category to be base + 1
                new_category_tree = f"{(int(current_tree) + 1):03d}"
                new_category_level = 0

            # If parent category was provided, find it
            else:
                parent = db.session.execute(
                    db.select(Category).where(Category.id == new_category_parent)
                ).scalar()

                # Determine the base of tree attribute for the new category

                # If parent has no subcategories, set base to 000
                if parent.subcategory_count == 0:
                    current_tree = "000"

                # Otherwise set base to tree attribute highest value among parent's subcategories
                else:
                    current_tree = db.session.execute(
                        db.select(Category.tree)
                        .where(Category.tree.like(f"{parent.tree}___"))
                        .order_by(Category.tree.desc())
                    ).scalar()

                # Set the tree attribute of new category to be base (last subcategory's tree) + 1
                new_category_tree = f"{parent.tree}{(int(current_tree[-3:]) + 1):03d}"

                new_category_level = parent.level + 1
                parent.subcategory_count += 1

            new_category = Category(
                name=new_category_name,
                level=new_category_level,
                tree=new_category_tree,
            )
            db.session.add(new_category)
            db.session.commit()

            return redirect(url_for("faq.manage_categories"))

        flash(error)

    categories = build_category_tree(load_categories())
    return render_template("category/add.html", categories=categories)


# Rename existing category
@bp.route("/cat/<int:id>/edit", methods=("GET", "POST"))
@login_required
@level_required(3)
def edit_category(id):
    category = get_category(id)

    if request.method == "POST":
        new_name = request.form["name"]
        error = None

        if not new_name:
            error = "Name is required."

        name_in_db = db.session.execute(
            db.select(Category.id).where(Category.name == new_name)
        ).scalar()
        if name_in_db and id != name_in_db:
            error = f"Category {new_name} already exists."

        if error is None:
            category.name = new_name
            db.session.commit()

            return redirect(url_for("faq.manage_categories"))

        flash(error)

    return render_template("category/rename.html", category=category)


# Delete existing category
@bp.route("/cat/<int:id>/delete", methods=("GET", "POST"))
@login_required
@level_required(3)
def delete_category(id):
    # Block deleting 'General' category
    if id == 1:
        flash(f"This category cannot be deleted")
        return redirect(url_for("faq.manage_categories"))

    # Pull category from db
    category = get_category(id)

    # Pull parent category from db
    if category.level == 0:
        parent_category = db.session.execute(
            db.select(Category).where(Category.id == 1)
        ).scalar()
    else:
        parent_category = category.get_parent()

    # If method is POST, delete the category
    if request.method == "POST":
        keep_notes = request.form["delete"]
        error = None

        # Ensure form wasn't tampered with
        if keep_notes not in ["keep", "delete"]:
            error = f'Unknown command "{keep_notes}"'

        if error is None:
            # Get a list of category and all its subcategories,
            # Then build a list of notes belonging to them
            if category.subcategory_count != 0:
                categories = (
                    db.session.execute(
                        db.select(Category).where(
                            Category.tree.like(f"{category.tree}%")
                        )
                    )
                    .scalars()
                    .all()
                )

                notes = []
                for cat in categories:
                    notes_in_cat = db.session.execute(
                        db.select(Note).where(Note.category == cat.id)
                    ).scalars()

                    if notes_in_cat is not None:
                        notes += notes_in_cat
            else:
                categories = category
                notes = db.session.execute(
                    db.select(Note).where(Note.category == categories.id)
                ).scalars()

            # If notes exist, edit or delete them
            if notes is not None:
                if keep_notes == "delete":
                    for note in notes:
                        db.session.delete(note)
                    db.session.commit()
                elif keep_notes == "keep":
                    for note in notes:
                        note.category = parent_category.id
                    db.session.commit()

            # Delete the category and its subcategories
            for cat in categories:
                db.session.delete(cat)
            db.session.commit()
            return redirect(url_for("faq.manage_categories"))

        flash(error)
    return render_template(
        "category/delete.html", category=category, parent=parent_category
    )


# Query the database for categories
def load_categories():
    return (
        db.session.execute(db.select(Category).order_by(Category.tree)).scalars().all()
    )


# Build the category tree for display
def build_category_tree(categories):
    # Create a dictionary of categories for reference, based on tree column
    tree_dict = {category.tree: category for category in categories}

    # Create a list of top level categories
    top_level_categories = []

    # Ensure each category has a subcategory attribute
    for category in categories:
        if not category.subcategories:
            category.subcategories = []

    # Build the category tree
    for category in categories:
        if category.level == 0:
            # Append top-level categories to the list
            top_level_categories.append(category)
        else:
            # Append subcategories to the proper parent
            parent_tree = category.get_parent_tree()
            tree_dict[parent_tree].subcategories.append(category)

    return top_level_categories


# Get a note by ID
def get_note(id):
    note = db.session.execute(
        db.select(Note, User.name).join(User).where(Note.id == id)
    ).scalar()

    if note is None:
        abort(404, "Note doesn't exist.")

    if note.author_id != g.user.id and g.user.permission_level < 3:
        abort(403, "You can only edit your own notes.")

    return note


# Get a category by ID
def get_category(id):
    category = db.session.execute(db.select(Category).where(Category.id == id)).scalar()

    if category is None:
        abort(404, "Category doesn't exist.")

    return category
