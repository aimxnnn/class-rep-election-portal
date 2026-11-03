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

#Afifa
#E1 - get all candidates
@app.get("/candidates")
def candidates(position = None, approved = True):
    return function.get_all_candidates(position=position, approved=approved)

#Afifa
#E2 - get 1 candidate by id
