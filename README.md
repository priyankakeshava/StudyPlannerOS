# StudyOS — Web Planner

StudyOS is a local-first student productivity web app built with **Flask + HTML/CSS/JavaScript + MySQL**. It does not use Streamlit.

## What is included

- Dashboard / Today
- Subjects & Topics with progress filters
- Topic detail view and prerequisite graph
- Automatic Study Planner
- Today / Week / Month planner views
- Automatic plan generation and saving
- Tasks & Exams with tabs and exam countdowns
- Weekly calendar with navigation
- Routine & Study Availability
- Revision Rotation with recurrence-based spacing
- Analytics with study-time bars and subject progress
- Local MySQL persistence

## Automatic planning

The planner combines:

- prerequisite eligibility and topological order
- upcoming exams and task deadlines
- routine blocks and one-off events
- existing study sessions
- a realistic 07:00–23:00 study window
- workload capacity checks
- conflict avoidance
- recurrence-based revision planning

Use **Generate plan** to build and save the next 7 days. Completing sessions changes the remaining state of the planner.

## Run locally

1. Create the database:
   `mysql -u root -p < database/schema.sql`
2. Copy `.env.example` to `.env` and enter your local MySQL credentials.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Start the app:
   `python server.py`
5. Open:
   `http://127.0.0.1:5000`

No cloud API or external service account is required for StudyOS itself.
