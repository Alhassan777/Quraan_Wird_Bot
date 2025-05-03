from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    language = Column(String, default='en')
    timezone = Column(String, default='UTC')
    streak = Column(Integer, default=0)
    last_check = Column(DateTime)
    reminder_time = Column(String)  # Format: "HH:MM"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    title = Column(String)
    language = Column(String, default='en')
    reminder_time = Column(String)  # Format: "HH:MM"
    reminder_set_by = Column(Integer)  # User ID who set the reminder
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GroupMember(Base):
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    streak = Column(Integer, default=0)
    last_check = Column(DateTime)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

class QuranQuote(Base):
    __tablename__ = 'quran_quotes'
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    surah = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Add backrefs
User.group_memberships = relationship("GroupMember", back_populates="user")
Group.members = relationship("GroupMember", back_populates="group") 