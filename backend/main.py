from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from functions import *
import functions

app = FastAPI(
    title = "Election Portal API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)


class Login(BaseModel):
    username: str
    password: str


class RegisterUser(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"


class NewCandidate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    roll_no: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    position: str
    manifesto: str = Field(min_length=30, max_length=500)


class WithdrawCandidate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    roll_no: str = Field(min_length=1, max_length=50)


class CastVote(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    voter_roll: str = Field(min_length=1, max_length=50)
    candidate_id: int


@app.post("/login")
def login(data: Login):
    tokens = functions.verify_login(data.username, data.password)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return tokens


@app.post("/refresh")
def refresh(refresh_token: str = Header(None)):
    payload = functions.verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = functions.get_user(payload["username"])
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    access = functions.create_token(user["username"], user["role"], "access")
    return {"access_token": access}


@app.post("/users", status_code=201)
def register_user(data: RegisterUser, token: str = Header(None)):
    authorize(token, OFFICER)
    check_choice(data.role, Roles, "role")
    user = functions.create_user(data.username, data.password, data.role)
    if user is None:
        raise HTTPException(status_code=409, detail="Username already exists")
    return user


#Aiman:
#E0: Creates a new election if it doesn't exist (additional)
@app.post("/election", status_code=201)
def create_new_election(token: str = Header(None)):
    authorize(token, OFFICER)
    if election_exists():
        raise HTTPException(400, "The election already exists.")
    return create_election()

# Afifa:
# E1 - Get all candidates
@app.get("/candidates")
def candidates(position=None, approved: bool = True, token: str = Header(None)):
    user = authorize(token, VIEW)
    check_choice(position, Positions, "position")
    if user["role"] == "student":
        approved = True
    return functions.get_all_candidates(position=position,approved=approved)

# Afifa:
# E2 - Get one candidate by ID
@app.get("/candidates/{candidate_id}")
def candidate(candidate_id: int, token: str = Header(None)):
    authorize(token, VIEW)

    result = functions.get_candidate_by_id(candidate_id)

    if result is None:
        raise HTTPException(status_code=404,detail="Candidate not found.")
    return result

#Aiman:
#E3: Nomiinates candidates
@app.post("/candidates", status_code=201)
def nominate(data: NewCandidate, token: str = Header(None)):
    user = authorize(token, STUDENT)
    roll_no = data.roll_no
    if roll_no != user["username"]:
        raise HTTPException(403, "Roll number does not match your login.")
    if data.position not in Positions:
        raise HTTPException(422, "Invalid position.")
    if get_phase() == "not created":
      raise HTTPException(400, "The election has not been created yet.")
    if get_phase() != "nominations":
        raise HTTPException(400, "Nominations are closed.")
    if find_active_candidate(roll_no):
        raise HTTPException(400, "This roll number is already a candidate.")

    return nominate_candidate(roll_no, data.name, data.position, data.manifesto)

# Afifa
# E4 - Approve a nomination
@app.patch("/candidates/{candidate_id}/approve")
def approve(candidate_id: int, token: str = Header(None)):
    authorize(token, OFFICER)

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(status_code=404,detail="Candidate not found.")

    if functions.get_phase() != "nominations":
        raise HTTPException(status_code=400,detail="Approving is only allowed during nominations.")

    if candidate["status"] != "nominated":
        raise HTTPException(status_code=400,detail="Only a nominated candidate can be approved.")

    return functions.approve_candidate(candidate_id)

# Afifa
# E5 - Withdraw a nomination
@app.patch("/candidates/{candidate_id}/withdraw")
def withdraw(candidate_id: int, data: WithdrawCandidate, token: str = Header(None)):
    user = authorize(token, STUDENT)

    if data.roll_no != user["username"]:
        raise HTTPException(status_code=403,detail="Roll number does not match your login.")

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(status_code=404,detail="Candidate not found.")

    if functions.get_phase() != "nominations":
        raise HTTPException(status_code=400,detail="Withdrawing is only allowed during nominations.")

    if candidate["roll_no"] != data.roll_no:
        raise HTTPException(status_code=403,detail="Roll number does not match this candidate.")

    if candidate["status"] != "nominated":
        raise HTTPException(status_code=400,detail="Only a nominated candidate can be withdrawn.")

    return functions.withdraw_candidate(candidate_id)


# Shaff:
#E6: Getting the current phase of the election
@app.get("/current_phase")
def current_phase(token: str = Header(None)):
    authorize(token, VIEW)
    phase = get_current_phase()
    if phase is None:
        raise HTTPException(status_code = 404, detail = "Election not found.")
    return {"current_phase": phase}

#Aiman:
#E7: Updates the election phase to the next phase 
@app.patch("/election/next-phase")
def next_phase(token: str = Header(None)):
    authorize(token, OFFICER)
    election_phase = get_phase()
    if election_phase not in Next_phase:
        raise HTTPException(400, "The election is already closed.")

    if election_phase == "nominations":
        for position in Positions:
            if count_approved(position) == 0:
                raise HTTPException(400, f"No approved candidate for {position}.")

    return change_phase(Next_phase[election_phase])

# Shaff:
#E8: Casting a vote
@app.post("/votes")
def vote(data: CastVote, token: str = Header(None)):
    user = authorize(token, STUDENT)
    if data.voter_roll != user["username"]:
        raise HTTPException(status_code = 403, detail = "Roll number does not match your login.")
    notif = cast_vote(data.voter_roll, data.candidate_id)
    if notif == "Voting is not currently open.":
        raise HTTPException(status_code = 400, detail = notif)
    if notif == "Candidate not found.":
        raise HTTPException(status_code = 404, detail = notif)
    if notif == "Candidate is not approved for voting.":
        raise HTTPException(status_code = 400, detail = notif)
    if notif.startswith("You have already voted for"):
        raise HTTPException(status_code = 400, detail = notif) 
    if notif == "Vote cast successfully.":
        return {"message": notif}
    else:
        raise HTTPException(status_code = 500, detail = "Unexpected result")

#Aiman:
#E9: Gives the positions that the voter has voted for
@app.get("/votes/{voter_roll}/positions")
def voted_positions(voter_roll: str, token: str = Header(None)):
    user = authorize(token, STUDENT)
    if user["username"] != voter_roll:
        raise HTTPException(status_code=403, detail="You can only view your own votes.")
    return {"voter_roll": voter_roll, "voted_positions": get_voted_positions(voter_roll)}

# Shaff:
#E10: Get the results
@app.get("/results")
def fetch_results(token: str = Header(None)):
    authorize(token, VIEW)
    phase = get_current_phase()
    if phase is None:
        raise HTTPException(status_code=404, detail="Election not found.")
    if phase != "closed":
        raise HTTPException(status_code=403, detail="Results are available only after the election is closed.")
    return get_results()




