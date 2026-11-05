from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import functions

app = FastAPI(title="Election Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Afifa
# E1 - Get all candidates
@app.get("/candidates")
def candidates(position=None, approved: bool = True):
    return functions.get_all_candidates(position=position,approved=approved)


# Afifa
# E2 - Get one candidate by ID
@app.get("/candidates/{candidate_id}")
def candidate(candidate_id: int):

    result = functions.get_candidate_by_id(candidate_id)

    if result is None:
        raise HTTPException(status_code=404,detail="Candidate not found.")
    return result


# Afifa
# E4 - Approve a nomination
@app.patch("/candidates/{candidate_id}/approve")
def approve(candidate_id: int):

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
def withdraw(candidate_id: int, roll_no: str):

    candidate = functions.get_candidate_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(status_code=404,detail="Candidate not found.")

    if functions.get_phase() != "nominations":
        raise HTTPException(status_code=400,detail="Withdrawing is only allowed during nominations.")

    if candidate["roll_no"] != roll_no:
        raise HTTPException(status_code=403,detail="Roll number does not match this candidate.")

    if candidate["status"] != "nominated":
        raise HTTPException(status_code=400,detail="Only a nominated candidate can be withdrawn.")

    return functions.withdraw_candidate(candidate_id)
