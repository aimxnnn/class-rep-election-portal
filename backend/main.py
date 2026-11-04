# API code goes here
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from functions import *

app = FastAPI(
    title = "Election Portal API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.get("/current_phase")
def current_phase():
    phase = get_current_phase()
    if phase is None:
        raise HTTPException(status_code = 404, detail = "Election not found.")
    return {"current_phase": phase}

@app.post("/votes")
def vote(voter_roll: str, candidate_id: int):
    notif = cast_vote(voter_roll, candidate_id)
    if notif == "Voting is not currently open.":
        raise HTTPException(status_code = 403, detail = notif)
    if notif == "Candidate not found.":
        raise HTTPException(status_code = 404, detail = notif)
    if notif == "Candidate is not approved for voting.":
        raise HTTPException(status_code = 403, detail = notif)
    if notif == "You have already voted for this position.":
        raise HTTPException(status_code = 403, detail = notif) 
    if notif == "Vote cast successfully.":
        return {"message": notif}
    else:
        raise HTTPException(status_code = 500, detail = "Unexpected result")

@app.get("/results")
def fetch_results():
    if get_current_phase() != "closed":
        raise HTTPException(status_code=403, detail="Results are available only after the election is closed.")
    return get_results()

