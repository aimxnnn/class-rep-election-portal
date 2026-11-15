from sqlalchemy.orm import Session
from tables import engine, Candidates, Votes, Election, Positions, Next_phase, Users
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt


ph = PasswordHasher()

SECRET_KEY = "shush"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60


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
        return "You have already voted for this position."

    session.add(Votes(position=candidate.position, candidate_id=candidate_id, voter_roll=voter_roll))
    session.commit()
    session.close()
    return "Vote cast successfully."


# Shaff
def get_results():
    session = Session(engine)
    response = []

    for position in Positions:
        candidates = session.query(Candidates).filter(Candidates.position == position, Candidates.status == "approved").all()
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


# Aiman
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
    existing = session.query(Candidates).filter(Candidates.roll_no == roll_no, Candidates.status != "withdrawn").first()
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
    count = session.query(Candidates).filter(Candidates.position == position, Candidates.status == "approved").count()
    session.close()
    return count


def change_phase(new_phase):
    session = Session(engine)
    election = session.query(Election).first()

    if election is None:
        session.close()
        return None

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

    candidates_query = session.query(Candidates)

    if position in Positions:
        candidates_query = candidates_query.filter(Candidates.position == position)

    if approved:
        candidates_query = candidates_query.filter(Candidates.status == "approved")

    candidates = candidates_query.all()
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


# Authentication - Registration
def register_user(roll_no, name, password):
    session = Session(engine)
    user_exists = session.query(Users).filter_by(roll_no=roll_no).first()

    if user_exists is not None:
        session.close()
        return False

    hashed_password = ph.hash(password)
    new_user = Users(roll_no=roll_no, name=name, password=hashed_password, role="student")

    session.add(new_user)
    session.commit()
    session.close()
    return True


# Authentication - Login
def verify_login(roll_no, password):
    session = Session(engine)
    user = session.query(Users).filter_by(roll_no=roll_no).first()

    if user is None:
        session.close()
        return False

    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        session.close()
        return False

    user_roll = user.roll_no
    user_name = user.name
    user_role = user.role
    session.close()

    access_token = create_token(roll_no=user_roll, name=user_name, role=user_role, token_type="access")
    refresh_token = create_token(roll_no=user_roll, name=user_name, role=user_role, token_type="refresh")

    return {"access_token": access_token, "refresh_token": refresh_token}


# Authentication - Create JWT
def create_token(roll_no, name, role, token_type):
    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY
    else:
        time = ACCESS_TOKEN_EXPIRY

    payload = {
        "roll_no": roll_no,
        "name": name,
        "role": role,
        "token_type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=time)
    }

    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token


# Authentication - Verify JWT
def verify_token(token, token_type):
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return False

    if payload.get("token_type") == token_type and "roll_no" in payload and "name" in payload and "role" in payload:
        return {"roll_no": payload["roll_no"], "name": payload["name"], "role": payload["role"]}

    return False
