from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from config.settings import config

# PostgreSQL
engine = create_engine(config.DATABASE_URL, pool_size=20, max_overflow=40)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

# Redis
redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

# Database helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()