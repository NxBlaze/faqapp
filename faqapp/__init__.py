from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from faqapp.extensions import db


# Create the app
def create_app(config_Class=Config):
    app = Flask(__name__)
    app.config.from_object(config_Class)

    # Initialize database
    db.init_app(app)

    # Import models and create database tables
    from faqapp.models import User, Note, Category

    with app.app_context():
        db.create_all()

        # Create general category to start with
        general_category = db.session.execute(
            db.select(Category).where(Category.name == "General")
        ).scalar()

        if general_category is None:
            general_category = Category(
                name="General",
                level=0,
                tree="000",
            )
            db.session.add(general_category)
            db.session.commit()

        # Create default admin user under id = 1
        admin = db.session.execute(
            db.select(User).where(User.id == 1)
        ).scalar()

        if admin is None:
            admin = User(
                id = 1,
                name = config_Class.ADMIN_USER,
                permission_level = 4,
                hash = generate_password_hash(config_Class.ADMIN_PW)
            )
            db.session.add(admin)
            db.session.commit()

    # Register blueprints
    from . import faq

    app.register_blueprint(faq.bp)

    from . import auth

    app.register_blueprint(auth.bp)

    from . import users

    app.register_blueprint(users.bp)

    return app
