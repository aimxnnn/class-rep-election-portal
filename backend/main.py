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

#E0: Creates a new election if it doesn't exist (additional)
@app.post("/election", status_code=201)
def create_new_election():
    if election_exists():
        raise HTTPException(400, "The election already exists.")
    return create_election()

#E3: Nomiinates candidates: 
@app.post("/candidates", status_code=201)
def nominate(roll_no: str, name: str, position: str, manifesto: str):
    if roll_no.strip() == "" or name.strip() == "" or manifesto.strip() == "":
        raise HTTPException(422, "All fields are required.")
    if position not in Positions:
        raise HTTPException(422, "Invalid position.")
    if len(manifesto) < 30:
        raise HTTPException(422, "Manifesto must be at least 30 characters.")
    if get_phase() == "not created":
      raise HTTPException(400, "The election has not been created yet.")
    if get_phase() != "nominations":
        raise HTTPException(400, "Nominations are closed.")
    if find_active_candidate(roll_no):
        raise HTTPException(400, "This roll number is already a candidate.")

    return nominate_candidate(roll_no, name, position, manifesto)

#E7: Updates the election phase to the next phase: 
@app.patch("/election/next-phase")
def next_phase():
    election_phase = get_phase()
    if election_phase not in Next_phase:
        raise HTTPException(400, "The election is already closed.")

    if election_phase == "nominations":
        for position in Positions:
            if count_approved(position) == 0:
                raise HTTPException(400, f"No approved candidate for {position}.")

    return change_phase(Next_phase[election_phase])

#E9: Gives the positions that the voter has voted for: 
@app.get("/votes/{voter_roll}/positions")
def voted_positions(voter_roll):
    return {"voter_roll": voter_roll, "voted_positions": get_voted_positions(voter_roll)}