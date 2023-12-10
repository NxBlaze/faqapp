import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "dev"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "faqapp.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USER = "admin"
    ADMIN_PW = "admin"