#Functions code goes here
from sqlalchemy import String, Integer, Column, create_engine, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

DB_PATH = "classrep.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

class votes(Base):
    __tablename__ = "votes"
    id = Column(Integer,primary_key=True)
    position = Column(String)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    voter_roll = Column(String)
    voted_on = Column(DateTime, default=datetime)
