from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Model representing a user of the bot."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    username = Column(String(64), nullable=True)
    timezone = Column(String(32), default="America/Los_Angeles")
    streak = Column(Integer, default=0)
    last_check = Column(DateTime, nullable=True)
    reminder_time = Column(String(5), nullable=True)  # Format: HH:MM
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, streak={self.streak})>"


class Group(Base):
    """Model representing a Telegram group."""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=True)
    reminder_time = Column(String(5), nullable=True)  # Format: HH:MM
    reminder_set_by = Column(Integer, ForeignKey("users.telegram_id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.id}, telegram_id={self.telegram_id}, title={self.title})>"


class GroupMember(Base):
    """Model representing a user's membership in a group."""
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.telegram_id"), nullable=False)
    streak = Column(Integer, default=0)
    last_check = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="members")
    
    def __repr__(self):
        return f"<GroupMember(user_id={self.user_id}, group_id={self.group_id}, streak={self.streak})>"


class QuranQuote(Base):
    """Model for storing Quran quotes for reminders."""
    __tablename__ = "quran_quotes"
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<QuranQuote(id={self.id})>" 