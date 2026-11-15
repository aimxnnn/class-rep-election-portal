
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from functions import *
import functions
from pydantic import BaseModel


app = FastAPI(title="Election Portal API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class RegisterUser(BaseModel):
    roll_no: str
    name: str
    password: str


class Login(BaseModel):
    roll_no: str
    password: str


# Authentication and RBAC Helpers
def get_logged_in_user(token):
    if not token:
        raise HTTPException(status_code=401, detail="Token required.")

    user = functions.verify_token(token=token, token_type="access")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return user


def check_admin(token):
    user = get_logged_in_user(token)

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    return user


def check_student(token):
    user = get_logged_in_user(token)

    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required.")

    return user


# Authentication Routes
@app.post("/register")
def register(user: RegisterUser):
    result = functions.register_user(roll_no=user.roll_no, name=user.name, password=user.password)

    if result is False:
        raise HTTPException(status_code=400, detail="User already exists.")

    return {"message": "Registration successful."}


@app.post("/login")
def login(user: Login):
    result = functions.verify_login(roll_no=user.roll_no, password=user.password)

    if result is False:
        raise HTTPException(status_code=401, detail="Invalid roll number or password.")

    return result


@app.post("/refresh")
def refresh(token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required.")

    user = functions.verify_token(token=token, token_type="refresh")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    new_access_token = functions.create_token(roll_no=user["roll_no"], name=user["name"], role=user["role"], token_type="access")

    return {"access_token": new_access_token}


# Aiman
# E0 - Create a new election.
@app.post("/election", status_code=201)
def create_new_election(token: str = Header(None)):
    check_admin(token)

    if election_exists():
        raise HTTPException(status_code=400, detail="The election already exists.")

    return create_election()


# Afifa
# E1 - Get all candidates.
@app.get("/candidates")
def candidates(position=None, approved: bool = True, token: str = Header(None)):
    user = get_logged_in_user(token)

    if user["role"] == "student":
        approved = True

    return functions.get_all_candidates(position=position, approved=approved)


# Afifa
# E2 - Get one candidate by ID.
@app.get("/candidates/{candidate_id}")
def candidate(candidate_id: int, token: str = Header(None)):
    get_logged_in_user(token)

    result = functions.get_candidate_by_id(candidate_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    return result


# Aiman
# E3 - Nominate a candidate.
@app.post("/candidates", status_code=201)
def nominate(position: str, manifesto: str, token: str = Header(None)):
    user = check_student(token)

    if position not in Positions:
        raise HTTPException(status_code=422, detail="Invalid position.")

    if manifesto.strip() == "":
        raise HTTPException(status_code=422, detail="Manifesto is required.")

    if len(manifesto) < 30:
        raise HTTPException(status_code=422, detail="Manifesto must be at least 30 characters.")

    if get_phase() == "not created":
        raise HTTPException(status_code=400, detail="The election has not been created yet.")

    if get_phase() != "nominations":
        raise HTTPException(status_code=400, detail="Nominations are closed.")

    if find_active_candidate(user["roll_no"]):
        raise HTTPException(status_code=400, detail="This roll number is already a candidate.")

    return nominate_candidate(user["roll_no"], user["name"], position, manifesto)


# Afifa
# E4 - Approve a nomination.
@app.patch("/candidates/{candidate_id}/approve")
def approve(candidate_id: int, token: str = Header(None)):
    check_admin(token)

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    if functions.get_phase() != "nominations":
        raise HTTPException(status_code=400, detail="Approving is only allowed during nominations.")

    if candidate["status"] != "nominated":
        raise HTTPException(status_code=400, detail="Only a nominated candidate can be approved.")

    return functions.approve_candidate(candidate_id)


# Afifa
# E5 - Withdraw a nomination.
@app.patch("/candidates/{candidate_id}/withdraw")
def withdraw(candidate_id: int, token: str = Header(None)):
    user = check_student(token)

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    if functions.get_phase() != "nominations":
        raise HTTPException(status_code=400, detail="Withdrawing is only allowed during nominations.")

    if candidate["roll_no"] != user["roll_no"]:
        raise HTTPException(status_code=403, detail="You can only withdraw your own nomination.")

    if candidate["status"] != "nominated":
        raise HTTPException(status_code=400, detail="Only a nominated candidate can be withdrawn.")

    return functions.withdraw_candidate(candidate_id)


# Shaff
# E6 - Get the current phase of the election.
@app.get("/current_phase")
def current_phase(token: str = Header(None)):
    get_logged_in_user(token)

    phase = get_current_phase()

    if phase is None:
        raise HTTPException(status_code=404, detail="Election not found.")

    return {"current_phase": phase}


# Aiman
# E7 - Update the election phase.
@app.patch("/election/next-phase")
def next_phase(token: str = Header(None)):
    check_admin(token)

    election_phase = get_phase()

    if election_phase not in Next_phase:
        raise HTTPException(status_code=400, detail="The election is already closed or has not been created.")

    if election_phase == "nominations":
        for position in Positions:
            if count_approved(position) == 0:
                raise HTTPException(status_code=400, detail=f"No approved candidate for {position}.")

    return change_phase(Next_phase[election_phase])


# Shaff
# E8 - Cast a vote.
@app.post("/votes")
def vote(candidate_id: int, token: str = Header(None)):
    user = check_student(token)

    notif = cast_vote(user["roll_no"], candidate_id)

    if notif == "Voting is not currently open.":
        raise HTTPException(status_code=403, detail=notif)

    if notif == "Candidate not found.":
        raise HTTPException(status_code=404, detail=notif)

    if notif == "Candidate is not approved for voting.":
        raise HTTPException(status_code=403, detail=notif)

    if notif == "You have already voted for this position.":
        raise HTTPException(status_code=403, detail=notif)

    if notif == "Vote cast successfully.":
        return {"message": notif}

    raise HTTPException(status_code=500, detail="Unexpected result.")


# Aiman
# E9 - Get the positions voted for by the logged-in student.
@app.get("/votes/positions")
def voted_positions(token: str = Header(None)):
    user = check_student(token)

    return {"voter_roll": user["roll_no"], "voted_positions": get_voted_positions(user["roll_no"])}


# Shaff
# E10 - Get the election results.
@app.get("/results")
def fetch_results(token: str = Header(None)):
    get_logged_in_user(token)

    phase = get_current_phase()

    if phase is None:
        raise HTTPException(status_code=404, detail="Election not found.")

    if phase != "closed":
        raise HTTPException(status_code=403, detail="Results are available only after the election is closed.")

    return get_results()
