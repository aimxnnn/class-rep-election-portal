from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session
from tables import *

ph = PasswordHasher()

OFFICER = ["officer"]
STUDENT = ["student"]
VIEW = ["officer", "student"]

OFFICER_USERNAME = "officer"
OFFICER_PASSWORD = "officer12345"

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY = "devshhh"
ALGORITHM = "HS256"


def hash_password(password):
    return ph.hash(password)


def check_password(password, password_hash):
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_user(username, password, role):
    session = Session(engine)
    old = session.query(Users).filter(Users.username == username).first()
    if old:
        session.close()
        return None
    user = Users(username=username, password_hash=hash_password(password), role=role)
    session.add(user)
    session.commit()
    result = {"username": user.username, "role": user.role}
    session.close()
    return result


def get_user(username):
    session = Session(engine)
    user = session.query(Users).filter(Users.username == username).first()
    if user is None:
        session.close()
        return None
    result = {"username": user.username, "role": user.role}
    session.close()
    return result


def seed_officer():
    session = Session(engine)
    first = session.query(Users).first()
    session.close()
    if first is None:
        create_user(OFFICER_USERNAME, OFFICER_PASSWORD, "officer")


seed_officer()


def create_token(username, role, token_type):
    mins = ACCESS_TOKEN_EXPIRY
    if token_type == "refresh":
        mins = REFRESH_TOKEN_EXPIRY
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=mins),
        "token_type": token_type,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token, token_type):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("token_type") != token_type:
        return None
    return payload


def verify_login(username, password):
    session = Session(engine)
    user = session.query(Users).filter(Users.username == username).first()
    if user is None:
        session.close()
        return None
    name = user.username
    role = user.role
    hashed = user.password_hash
    session.close()
    if not check_password(password, hashed):
        return None
    return {
        "access_token": create_token(name, role, "access"),
        "refresh_token": create_token(name, role, "refresh"),
    }


def authorize(token, roles):
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload["role"] not in roles:
        raise HTTPException(status_code=403, detail="You do not have permission for this action")
    return payload


def check_choice(value, allowed, field):
    if value is not None and value not in allowed:
        raise HTTPException(status_code=422, detail=field + " must be one of " + str(allowed))


# Shaff
def get_current_phase():
    session = Session(engine)
    election = session.query(Election).first()
    session.close()
    if election:
        return election.phase
    else:
        return None

# Shaff
def cast_vote(voter_roll, candidate_id):
    if get_current_phase() != "voting":
        return "Voting is not currently open."
    session = Session(engine)
    candidate = session.query(Candidates).filter(Candidates.id == candidate_id).first()
    if not candidate:
        session.close()
        return "Candidate not found."

    if candidate.status != "approved":
        session.close()
        return "Candidate is not approved for voting."

    already_voted = session.query(Votes).filter(Votes.voter_roll == voter_roll, Votes.position == candidate.position).first()
    if already_voted:
        session.close()
        return "You have already voted for " + candidate.position + "."
    else:
        session.add(Votes(position=candidate.position, candidate_id=candidate_id, voter_roll=voter_roll))
        session.commit()
        session.close()
        return "Vote cast successfully."

# Shaff
def get_results():
    session = Session(engine)
    response = []

    for position in Positions:
        candidates = session.query(Candidates).filter(Candidates.position == position,Candidates.status == "approved").all()

        position_results = []

        for candidate in candidates:
            vote_count = session.query(Votes).filter(Votes.candidate_id == candidate.id).count()

            temp_candidate = {
                "id": candidate.id,
                "name": candidate.name,
                "roll_no": candidate.roll_no,
                "position": candidate.position,
                "status": candidate.status,
                "vote_count": vote_count
            }

            position_results.append(temp_candidate)

        winner = None
        highest_votes = -1

        for candidate in position_results:
            if candidate["vote_count"] > highest_votes:
                highest_votes = candidate["vote_count"]
                winner = candidate

        temp_position = {
            "position": position,
            "candidates": position_results,
            "winner": winner
        }

        response.append(temp_position)

    session.close()
    return response

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

    query = session.query(Candidates)

    if position in Positions:
        query = query.filter(Candidates.position == position)

    if approved:
        query = query.filter(Candidates.status == "approved")

    candidates = query.all()

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


