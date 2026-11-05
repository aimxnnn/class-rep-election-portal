from sqlalchemy import String, Integer, Column, create_engine, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

db_path = "election.db"
engine = create_engine(f"sqlite:///{db_path}")
Base = declarative_base()

Positions = ["class_rep", "sports_secretary", "cultural_secretary", "tech_secretary"]
Statuses = ["nominated", "approved", "withdrawn"]
Phases = ["nominations", "voting", "closed"]
Next_phase = {"nominations": "voting", "voting": "closed"}

class Candidates(Base):
    __tablename__ = "Candidates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_no = Column(String)
    name = Column(String)
    position = Column(String)
    manifesto = Column(String(500))
    status = Column(String, default="nominated")
    nominated_on = Column(DateTime, default=datetime.now)

class Votes(Base): #Afifa
    __tablename__ = "Votes"
    id = Column(Integer,primary_key=True)
    position = Column(String)
    candidate_id = Column(Integer, ForeignKey("Candidates.id"))
    voter_roll = Column(String)
    voted_on = Column(DateTime, default=datetime.now)

class Election(Base):
    __tablename__ = "Elections"
    id = Column(Integer, primary_key=True)
    phase = Column(String, nullable=False, default="nominations")
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)

Base.metadata.create_all(engine)
