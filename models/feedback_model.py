from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from config.database_config import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(String(64), unique=True, nullable=False)
    translation_id = Column(Integer, ForeignKey("translations.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    english_text = Column(Text, nullable=False)
    original_limbu = Column(Text)
    suggested_limbu = Column(Text, nullable=False)
    suggested_script = Column(Text)
    suggested_pronunciation = Column(Text)

    feedback_type = Column(String(50))  # correction, addition, report
    confidence_score = Column(Float)
    status = Column(String(50), default="pending")  # pending, validated, rejected

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    translation = relationship("Translation", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
    validations = relationship(
        "Validation", back_populates="feedback", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False)
    email = Column(String(255))
    username = Column(String(100))

    user_type = Column(
        String(50), default="contributor"
    )  # contributor, native_speaker, expert, admin
    trust_score = Column(Float, default=0.5)
    total_contributions = Column(Integer, default=0)
    accepted_contributions = Column(Integer, default=0)

    is_verified = Column(Boolean, default=False)
    is_native_speaker = Column(Boolean, default=False)
    is_linguist = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    validations = relationship(
        "Validation", back_populates="validator", cascade="all, delete-orphan"
    )


class Validation(Base):
    __tablename__ = "validations"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    vote = Column(String(20))  # approve, reject, modify
    vote_weight = Column(Float, default=1.0)
    modification = Column(JSON)
    comment = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feedback = relationship("Feedback", back_populates="validations")
    validator = relationship("User", back_populates="validations")