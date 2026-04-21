from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from config.database_config import Base


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    english_text = Column(Text, nullable=False)
    limbu_text = Column(Text, nullable=False)
    limbu_script = Column(Text)
    pronunciation = Column(Text)
    method_used = Column(String(50))  # dictionary, ml, hybrid
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feedback = relationship(
        "Feedback", back_populates="translation", cascade="all, delete-orphan"
    )


class Dictionary(Base):
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True)
    english = Column(String(255), unique=True, nullable=False)
    limbu = Column(String(255), nullable=False)
    limbu_script = Column(String(255))
    pronunciation = Column(String(255))
    part_of_speech = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)

    # Relationships
    example_sentences = relationship("ParallelSentence", back_populates="dictionary")


class ParallelSentence(Base):
    __tablename__ = "parallel_sentences"

    id = Column(Integer, primary_key=True)
    dictionary_id = Column(Integer, ForeignKey("dictionary.id"), nullable=True)
    english = Column(Text, nullable=False)
    limbu = Column(Text, nullable=False)
    limbu_script = Column(Text)
    pronunciation = Column(Text)
    source = Column(String(100))  # manual, feedback, imported
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dictionary = relationship(
        "Dictionary",
        back_populates="example_sentences",
    )