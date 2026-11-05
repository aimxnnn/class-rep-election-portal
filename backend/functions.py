#Functions code goes here   
from sqlalchemy.orm import Session
from tables import engine, Candidates, Votes, Election, Positions, Next_phase

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