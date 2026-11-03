#Functions code goes here
from sqlalchemy.orm import Session
from tables import engine, Candidates, Votes, Election, Positions, Next_phase

#Afifa
#E1 - get all candidates filtered by position.
def get_all_candidates(position=None,approved=True):
    session = Session(engine)
    if position in Positions:
        if approved:
            candidates = session.query(Candidates).filter(Candidates.position==position, Candidates.status =="approved").all()
        else:
            candidates = session.query(Candidates).filter(Candidates.position==position).all()

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
    session.commit()    
    session.close()
    return response

#Afifa
#E2 - get 1 candidate by id.
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
    session.commit()
    session.close()
    return response

#Afifa
#E4 - approve a nomination.
def approve_candidate(candidate_id):
    session = Session(engine)
    candidate = session.get(Candidates, candidate_id)
    election = session.query(Election).first()
    if candidate is None:
        session.close()
        return 404, "Candidate not found."
    if election.phase != "nominations":
        session.close()
        return 400, "Approving is only allowed during nominations."
    if candidate.status != "nominated":
        session.close()
        return 400, "Only a nominated candidate can be approved."
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

#Afifa
#E5 - withdraw a nomination with the candidate's roll number.
def withdraw_candidate(candidate_id, roll_no):
    session = Session(engine)
    candidate = session.get(Candidates, candidate_id)
    election = session.query(Election).first()
    if candidate is None:
        session.close()
        return 404, "Candidate not found."
    if election.phase != "nominations":
        session.close()
        return 400, "Withdrawing is only allowed during nominations."
    if candidate.roll_no != roll_no:
        session.close()
        return 403, "Roll number does not match this candidate."
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

    





