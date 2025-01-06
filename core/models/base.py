from datetime import datetime

from sqlalchemy import ForeignKey, text, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):    
    __abstract__ = True 

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
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
    password: Mapped[bytes]
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), default=1, server_default=text("1"))
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
    
