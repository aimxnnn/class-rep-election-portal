from sqlalchemy import String, Integer, Column, create_engine, DateTime
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


Base.metadata.create_all(engine)
