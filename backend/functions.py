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


# Afifa
# E1 - Get all candidates, optionally filtered by position.
def get_all_candidates(position=None, approved=True):
    session = Session(engine)

    if position in Positions:
        if approved:
            candidates = session.query(Candidates).filter(Candidates.position == position,Candidates.status == "approved").all()
        else:
            candidates = session.query(Candidates).filter(Candidates.position == position).all()
    else:
        candidates = session.query(Candidates).all()

    response = []

    for candidate in candidates:
        temp_candidate = {
            "id": candidate.id,
            "roll_no": candidate.roll_no,
            "name": candidate.name,
            "position": candidate.position,
            "manifesto": candidate.manifesto,
            "status": candidate.status,
            "nominated_on": candidate.nominated_on
        }
        response.append(temp_candidate)

    session.close()
    return response


# E2 - Get one candidate by ID.
def get_candidate_by_id(candidate_id):
    session = Session(engine)

    candidate = session.get(Candidates, candidate_id)

    if candidate is None:
        session.close()
        return None

    response = {
        "id": candidate.id,
        "roll_no": candidate.roll_no,
        "name": candidate.name,
        "position": candidate.position,
        "manifesto": candidate.manifesto,
        "status": candidate.status,
        "nominated_on": candidate.nominated_on
    }

    session.close()
    return response



# E4 - Approve a nomination.
def approve_candidate(candidate_id):
    session = Session(engine)

    candidate = session.get(Candidates, candidate_id)

    if candidate is None:
        session.close()
        return None

    candidate.status = "approved"

    session.commit()

    response = {
        "id": candidate.id,
        "roll_no": candidate.roll_no,
        "name": candidate.name,
        "position": candidate.position,
        "manifesto": candidate.manifesto,
        "status": candidate.status,
        "nominated_on": candidate.nominated_on
    }

    session.close()
    return response


# E5 - Withdraw a nomination.
def withdraw_candidate(candidate_id):
    session = Session(engine)

    candidate = session.get(Candidates, candidate_id)

    if candidate is None:
        session.close()
        return None

    candidate.status = "withdrawn"

    session.commit()

    response = {
        "id": candidate.id,
        "roll_no": candidate.roll_no,
        "name": candidate.name,
        "position": candidate.position,
        "manifesto": candidate.manifesto,
        "status": candidate.status,
        "nominated_on": candidate.nominated_on
    }

    session.close()
    return response


