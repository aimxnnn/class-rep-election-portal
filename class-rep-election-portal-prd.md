# **15\. PRD & Design Doc: Class Rep Election**

Build an app to run the student council election, from nominations to results: a **FastAPI \+ SQLite** backend and a **React** frontend. **Team: 2 students. Time: 2 days, with the demo on day 3\.**

## **1\. What to build**

* The election moves through three phases: **nominations → voting → closed**.

* During nominations, students nominate themselves for one position with their **roll number** and a manifesto. The election officer approves nominations.

* During voting, each student votes once per position. Results show only after the election is closed. There are no logins.

## **2\. Data**

One SQLite file, election.db, with three tables.

| Table | Columns |
| :---- | :---- |
| candidates | id, roll\_no, name, position, manifesto, status, nominated\_on |
| votes | id, position, candidate\_id, voter\_roll, voted\_on |
| election | id, phase (one row only) |

position must be one of: class\_rep, sports\_secretary, cultural\_secretary, tech\_secretary. Candidate status is one of: nominated, approved, withdrawn. phase is one of: nominations, voting, closed.

Add **8 candidates** across all four positions (one withdrawn, one still waiting for approval) to start with. Start the election in nominations, with no votes.

## **3\. API: 10 endpoints**

Run it on port **8001**, and add CORS so the React app can call it.

**Before you write any code, fill in the empty columns.** Pick the method (GET, POST, PATCH or DELETE), the path, what the client sends, and the status codes. Use the rules in section 4 for the error codes.

| \# | What it does | Method | Path | Request body | Success code | Error codes |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| E1 | Get all the candidates. Can be filtered by position, and to show only approved ones. |  |  |  |  |  |
| E2 | Get one candidate by their id. |  |  |  |  |  |
| E3 | Nominate: roll number, name, position and manifesto. It starts as nominated. |  |  |  |  |  |
| E4 | Approve a nomination. |  |  |  |  |  |
| E5 | Withdraw a nomination, with the candidate's roll number. |  |  |  |  |  |
| E6 | Get the current phase. |  |  |  |  |  |
| E7 | Move the election to its next phase. |  |  |  |  |  |
| E8 | Cast a vote: voter's roll number and candidate. The position comes from the candidate. |  |  |  |  |  |
| E9 | Get the positions a student has already voted in, by roll number (not who they voted for). |  |  |  |  |  |
| E10 | Get the results: for each position, the votes for each candidate and the winner. |  |  |  |  |  |

## **4\. Rules the API must check**

| Rule | Status |
| :---- | :---- |
| Nominating, approving or withdrawing when the phase is not nominations | 400 |
| Nominating a roll number that is already a candidate (not withdrawn) | 400 |
| Approving a nomination that is not nominated | 400 |
| Withdrawing with a roll number that isn't the candidate's | 403 |
| Voting when the phase is not voting | 400 |
| Voting for a candidate who is not approved | 400 |
| Voting twice for the same position | 400 |
| Moving to voting when a position has no approved candidate, or moving on from closed | 400 |
| Asking for results before the election is closed | 403 |
| A candidate id that doesn't exist | 404 |
| A missing or empty field, a position not in the list, or a manifesto shorter than 30 characters | 422 |

Every error sends a clear message: {"detail": "You have already voted for class\_rep."}. 403 means "you're not allowed to do this".

Hint for the phase order: keep the next step in a dictionary, {"nominations": "voting", "voting": "closed"}. For results: SELECT candidate\_id, COUNT(\*) FROM votes GROUP BY candidate\_id.

## **5\. Frontend**

One page with three parts. Keep the API address in one place: const API\_URL \= "http\://127.0.0.1:8001";

| Part | Shows | Does | Uses |
| :---- | :---- | :---- | :---- |
| Vote | the phase as a banner at the top; approved candidates grouped by position; click one to read their manifesto; a "Voted" tick on positions already done | type roll number \+ **Show**; **Vote** button on each candidate | E1, E2, E6, E8, E9 |
| Nominate | a form with a position dropdown | adds a nomination; roll number \+ **Withdraw** | E3, E5 |
| Election officer | nominations waiting for approval; when closed, the results with the winner of each position | **Approve** button; **Next phase** button | E1, E4, E7, E10 |

* Put each component in its own file in src/components/.

* After every action, the page updates without a refresh.

* When the API says no, show its detail message on the page.

## **6\. Plan**

| Day | Finish |
| :---- | :---- |
| Day 1 | Database \+ all 10 endpoints \+ the rules, tested in /docs |
| Day 2 | React app connected to the API |
| Day 3 | Demo |

Fill in the progress check-in every 3 hours.

## **7\. Done when**

* ☐ All 10 endpoints work in /docs.

* ☐ Each rule in section 4 gives the right status code.

* ☐ Moving to the next phase updates the banner without a refresh, and voting marks that position as voted.

* ☐ Voting twice for a position shows the API's message on the page.

* ☐ The data is still there after restarting the API.

## **8\. Submit and marks**

One GitHub repo with backend/, frontend/ (without node\_modules) and a README.md that says how to run both. Both partners must be able to explain any part of the code.

| Part | Marks |
| :---- | :---- |
| Endpoints and rules | 40 |
| Frontend connected to the API | 40 |
| README and demo (explain your code) | 20 |

**Bonus, if you finish early:** voter turnout per position, a bar chart of the results, or pytest tests for the rules.