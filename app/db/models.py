from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(String, unique=True, index=True)
    key = Column(String, index=True)
    summary = Column(String)
    description = Column(Text)
    last_comment = Column(Text)
    time_spent = Column(String)
    labels = Column(String)
    organizations = Column(String)
    assignee = Column(String, index=True)
    due_date = Column(Date, index=True)
    extra_fields = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserOrganization(Base):
    __tablename__ = "user_organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    organization = Column(String, index=True)
