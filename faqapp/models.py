from datetime import datetime
from typing import List
from sqlalchemy import Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from faqapp.extensions import db


# Define user model
class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)
    permission_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    notes: Mapped[List["Note"]] = relationship(back_populates="author")


# Define note model
class Note(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id = mapped_column(ForeignKey("user.id"))
    create_date: Mapped[datetime] = mapped_column(
        insert_default=func.now(), nullable=False
    )
    update_date: Mapped[datetime] = mapped_column(
        insert_default=func.now(), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(String)
    category = mapped_column(ForeignKey("category.id"))

    author: Mapped["User"] = relationship(back_populates="notes")
    category_name: Mapped["Category"] = relationship(back_populates="notes")


# Define category model
class Category(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    tree: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    subcategory_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    notes: Mapped[List["Note"]] = relationship(back_populates="category_name")

    subcategories = []

    def get_parent_tree(self):
        return self.tree[:-3]

    def get_parent(self):
        return db.session.execute(
            db.select(Category).where(Category.tree == self.get_parent_tree())
        ).scalar()
