from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

class AuthUser(Base):
    __tablename__ = 'auth_users'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "customer", "kitchen", "sales", "delivery", "admin"
    is_active = Column(Boolean, default=True)
