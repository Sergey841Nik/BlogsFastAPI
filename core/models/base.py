from datetime import datetime

from sqlalchemy import ForeignKey, Text, text, TIMESTAMP, func, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class User(Base):
    __tablename__ = "users"

    phone_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), default=1, server_default=text("1")
    )
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")

    blogs: Mapped[list["Blog"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class Blog(Base):
    __tablename__ = "blogs"

    title: Mapped[str] = mapped_column(unique=True, nullable=False)
    author: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text)
    short_description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="published", server_default="published")

    user: Mapped["User"] = relationship("User", back_populates="blogs")

    tags: Mapped[list["Tag"]] = relationship(
        secondary="blog_tags", back_populates="blogs"
    )


class Tag(Base):
    __tablename__ = "tags"
    name: Mapped[str] = mapped_column(String(50), unique=True)

    blogs: Mapped[list["Blog"]] = relationship(
        secondary="blog_tags", back_populates="tags"
    )


class BlogTag(Base):
    __tablename__ = "blog_tags"
    __table_args__ = (UniqueConstraint("blog_id", "tag_id", name="uq_blog_tag"),)

    blog_id: Mapped[int] = mapped_column(
        ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False
    )
