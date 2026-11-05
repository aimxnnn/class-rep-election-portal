from sqlalchemy.orm import Session
from tables import engine, Candidates, Votes, Election, Positions, Next_phase


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


# Afifa
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


# Afifa
# Get the current election phase.
def get_phase():
    session = Session(engine)

    election = session.query(Election).first()

    if election is None:
        session.close()
        return "not created"

    response = election.phase

    session.close()
    return response


# Afifa
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


# Afifa
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


