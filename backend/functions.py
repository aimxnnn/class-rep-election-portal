from sqlalchemy.orm import Session
from tables import *

#Aiman 
def election_exists():
    session = Session(engine)
    count = session.query(Election).count()
    session.close()
    return count > 0

def create_election():
    session = Session(engine)
    election = Election(phase="nominations")
    session.add(election)
    session.commit()
    session.close()
    return {"message": "Election created successfully", "phase": "nominations"}

def get_phase():
    session = Session(engine)
    election = session.query(Election).first()
    if election is None:
        session.close()
        return "not created"
    election_phase = election.phase
    session.close()
    return election_phase

def find_active_candidate(roll_no):
    session = Session(engine)
    existing = session.query(Candidates).filter(
        Candidates.roll_no == roll_no,
        Candidates.status != "withdrawn",
    ).first()
    session.close()
    return existing

def nominate_candidate(roll_no, name, position, manifesto):
    session = Session(engine)
    candidate = Candidates(roll_no=roll_no, name=name, position=position, manifesto=manifesto)
    session.add(candidate)
    session.commit()
    candidate_id = candidate.id
    session.close()
    return {"message": "Candidate nominated successfully", "candidate_id": candidate_id}

def count_approved(position):
    session = Session(engine)
    count = session.query(Candidates).filter(
        Candidates.position == position,
        Candidates.status == "approved",
    ).count()
    session.close()
    return count

def change_phase(new_phase):
    session = Session(engine)
    election = session.query(Election).first()
    election.phase = new_phase
    session.commit()
    session.close()
    return {"message": "Phase changed successfully", "phase": new_phase}

def get_voted_positions(voter_roll):
    session = Session(engine)
    votes = session.query(Votes).filter(Votes.voter_roll == voter_roll).all()
    positions = []
    for vote in votes:
        positions.append(vote.position)
    session.close()
    return positions

