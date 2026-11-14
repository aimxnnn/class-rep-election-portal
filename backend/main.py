from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import functions
from tables import Positions, Next_phase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class RegisterRequest(BaseModel):
    roll_no: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    roll_no: str
    password: str


class NominationRequest(BaseModel):
    name: str = Field(min_length=1)
    position: str
    manifesto: str = Field(min_length=30, max_length=500)


class VoteRequest(BaseModel):
    candidate_id: int = Field(gt=0)


# AUTHENTICATION HELPERS

# Get logged-in user's details using JWT
def get_logged_in_user(authorization):

    if authorization is None:
        raise HTTPException(status_code=401, detail="Please login first.")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header."
        )

    token = authorization.replace("Bearer ", "", 1)

    user = functions.verify_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token."
        )

    return user


# Check whether the user is an admin
def check_admin(user):

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )


# Check whether the user is a student
def check_student(user):

    if user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access required."
        )


# REGISTER AND LOGIN 

@app.post("/register", status_code=201)
def register(data: RegisterRequest):

    # Check roll number
    if not data.roll_no.startswith("R") or not data.roll_no[1:].isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid roll number."
        )

    # Register the student
    result = functions.register_user(
        data.roll_no,
        data.password
    )

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="User already exists."
        )

    return {"message": result}

# LOGIN

@app.post("/login")
def login(data: LoginRequest):

    result = functions.login_user(
        data.roll_no,
        data.password
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid roll number or password."
        )

    return result


# E0: CREATE ELECTION 

@app.post("/election")
def add_election(authorization: str = Header(None)):

    user = get_logged_in_user(authorization)
    check_admin(user)

    if functions.election_exists():
        raise HTTPException(
            status_code=400,
            detail="Election already exists."
        )

    return functions.create_election()


# E1: GET ALL CANDIDATES 

@app.get("/candidates")
def get_candidates(position: str = None):

    if position is not None and position not in Positions:
        raise HTTPException(
            status_code=400,
            detail="Invalid position."
        )

    return functions.get_all_candidates(
        position=position,
        approved=True
    )


# E2: GET CANDIDATE BY ID 

@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int):

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    return candidate


# E3: NOMINATE CANDIDATE 

@app.post("/candidates")
def add_candidate(
    data: NominationRequest,
    authorization: str = Header(None)
):

    user = get_logged_in_user(authorization)
    check_student(user)

    roll_no = user["roll_no"]

    if data.position not in Positions:
        raise HTTPException(
            status_code=400,
            detail="Invalid position."
        )

    if not functions.election_exists():
        raise HTTPException(
            status_code=404,
            detail="Election does not exist."
        )

    if functions.get_phase() != "nominations":
        raise HTTPException(
            status_code=400,
            detail="Nominations are closed."
        )

    existing_candidate = functions.find_active_candidate(roll_no)

    if existing_candidate:
        raise HTTPException(
            status_code=400,
            detail="You already have an active nomination."
        )

    return functions.nominate_candidate(
        roll_no,
        data.name,
        data.position,
        data.manifesto
    )


# E4: APPROVE CANDIDATE 

@app.patch("/candidates/{candidate_id}/approve")
def approve(
    candidate_id: int,
    authorization: str = Header(None)
):

    user = get_logged_in_user(authorization)
    check_admin(user)

    if functions.get_phase() != "nominations":
        raise HTTPException(
            status_code=400,
            detail="Nominations are closed."
        )

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    if candidate["status"] != "nominated":
        raise HTTPException(
            status_code=400,
            detail="Candidate cannot be approved."
        )

    return functions.approve_candidate(candidate_id)


# E5: WITHDRAW CANDIDATE

@app.patch("/candidates/{candidate_id}/withdraw")
def withdraw(
    candidate_id: int,
    authorization: str = Header(None)
):

    user = get_logged_in_user(authorization)
    check_student(user)

    if functions.get_phase() != "nominations":
        raise HTTPException(
            status_code=400,
            detail="Nominations are closed."
        )

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    if candidate["roll_no"] != user["roll_no"]:
        raise HTTPException(
            status_code=403,
            detail="You can only withdraw your own nomination."
        )

    if candidate["status"] != "nominated":
        raise HTTPException(
            status_code=400,
            detail="Candidate cannot be withdrawn."
        )

    return functions.withdraw_candidate(candidate_id)


#  E6: GET CURRENT PHASE 

@app.get("/current_phase")
def current_phase():

    phase = functions.get_phase()

    if phase is None:
        raise HTTPException(
            status_code=404,
            detail="Election does not exist."
        )

    return {"phase": phase}


# E7: CHANGE ELECTION PHASE 

@app.patch("/election/next-phase")
def next_phase(authorization: str = Header(None)):

    user = get_logged_in_user(authorization)
    check_admin(user)

    current = functions.get_phase()

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="Election does not exist."
        )

    if current not in Next_phase:
        raise HTTPException(
            status_code=400,
            detail="Election is already closed."
        )

    new_phase = Next_phase[current]

    if current == "nominations":

        for position in Positions:

            approved_count = functions.count_approved(position)

            if approved_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No approved candidates for {position}."
                )

    return functions.change_phase(new_phase)


# 8: CAST VOTE 

@app.post("/votes")
def vote(
    data: VoteRequest,
    authorization: str = Header(None)
):

    user = get_logged_in_user(authorization)
    check_student(user)

    result = functions.cast_vote(
        user["roll_no"],
        data.candidate_id
    )

    if result == "Election does not exist.":
        raise HTTPException(status_code=404, detail=result)

    if result != "Vote cast successfully.":
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


# 9: GET MY VOTED POSITIONS 

@app.get("/votes/my-positions")
def my_voted_positions(authorization: str = Header(None)):

    user = get_logged_in_user(authorization)
    check_student(user)

    return functions.get_voted_positions(user["roll_no"])


# 10: GET ELECTION RESULTS

@app.get("/results")
def results():

    phase = functions.get_phase()

    if phase != "closed":
        raise HTTPException(
            status_code=403,
            detail="Results are available only after the election is closed."
        )

    return functions.get_results()
