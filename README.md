# Healthcare_Monitoring_AI_Agent
Healthcare Monitoring AI Agent (Medication + Health Records + Fitness Tracking)

A lightweight, modular personal-health monitoring system built using Python, Streamlit, and SQLite, with a clean agent-based backend architecture.
----------------------------------------------------------------------------

🔗 Table of Contents

Overview

Key Features

System Architecture

Tech Stack

Project Structure

Database Schema

How to Run

Core Modules

Screenshots

Future Improvements

Contributors
-----------------------------------------------------------------------------------------

⭐ Overview

This project is a Healthcare Monitoring AI Agent that helps users manage their medications, track health readings, monitor fitness activity, and receive basic analytics.

It consists of:

A Streamlit front-end dashboard

A DB handler (db.py)

An Agent layer (agent.py)

A SQL-backed model layer (optional)


The system is flexible:
→ You can use either SQLite (db.py) or SQLAlchemy models.
→ The UI adapts automatically to whichever backend is available.
------------------------------------------------------------------------------------------------------------------

⚡ Key Features

🩺 Health Records Tracking

Add BP, Sugar, Weight records

View last 7 days of records

Automatic detection of:

High BP

Emergency levels

High sugar

Low sugar



💊 Medication Management

Add medications with time, dose, frequency

Delete medications

Mark medication as taken

Track how many times taken recently

Reminder: meds due within ±1 hour


🏃 Fitness Tracking

Add steps + calories

CSV upload for bulk import

Daily step chart

7-day average calculation


🤖 AI Agent Layer

Encapsulates all DB operations

Provides clean APIs:

list_users

add_medication

list_med_taken

add_fitness_record

list_fitness_records



📊 Analytics (Day 5 Work)

Avg systolic/diastolic (7 days)

Avg sugar

Avg steps

Visual charts for BP, sugar, steps



---

🧱 System Architecture

┌──────────────────────────┐
                  │       Streamlit UI       │
                  └─────────────┬────────────┘
                                │
                                ▼
                  ┌──────────────────────────┐
                  │       Agent Layer        │
                  │   (agent.py: HealthAgent)│
                  └─────────────┬────────────┘
                                │
                                ▼
      ┌───────────────────────────────────────────────────┐
      │                        Backend                    │
      │  db.py (SQLite Helper)         models.py (ORM)    │
      └───────────────────────────────────────────────────┘
                                │
                                ▼
                      SQLite Database (health.db)

--------------------------------------------------------------------------------

🛠 Tech Stack

Layer	Technology

Frontend	Streamlit
Backend Logic	Python Agent
Database	SQLite
ORM (optional)	SQLAlchemy
Analytics	Pandas, Charts
Timezone Handling	IST + UTC aware timestamps

--------------------------------------------------------------------------------------


📁 Project Structure

Healthcare_Monitoring_AI_Agent/
│
├── app.py                 # Main Streamlit UI
├── agent.py               # HealthAgent wrapper
├── db.py                  # SQLite database operations
├── models.py              # (Optional) SQLAlchemy models
├── seed_data.py           # Sample data for first run
├── app_utils.py           # BP/Sugar parsing helpers
├── README.md              # Documentation
└── requirements.txt       # Dependencies

-------------------------------------------------------------------------------------

🗄 Database Schema

users

Column	Type

id	INTEGER
name	TEXT
dob	TEXT
phone	TEXT
created_at	TEXT


medications

Column

id
user_id
name
dose
times
frequency
notes


health_records

Column

id
user_id
type (bp/sugar/weight)
value
recorded_at


fitness_records

Column

id
user_id
steps
calories
record_date


med_taken (Day 7 addition)

Column

id
user_id
medication_id
taken_at
note

-------------------------------------------------------------------------------------------------

▶ How to Run

1. Create virtual environment

python -m venv venv

2. Activate environment

Windows:

venv\Scripts\activate

3. Install requirements

pip install -r requirements.txt

4. Run Streamlit

streamlit run app.py

-----------------------------------------------------------------------------------------------------

🔧 Core Modules

1. agent.py

Handles:

Adding medications

Adding health records

Adding fitness records

Marking medications taken

Listing data


Acts as a clean interface between UI ↔ DB.


----------------------------------------------------------------------------------------------------------

2. db.py

Low-level DB functions:

CRUD for medications

CRUD for fitness_records

CRUD for health_records

med_taken tracking



-------------------------------------------------------------------------------------------------------------

3. app.py

The main UI:

Sidebar for user selection

Medication form + list

Fitness form + charts

Health record form

Alerts

Analytics

Reminders


-----------------------------------------------------------------------------------------------------------

🖼 Screenshots

(You can add actual screenshots here)

[ Dashboard ]
[ Add Medication Form ]
[ Analytics Charts ]
[ Fitness Logs ]


-------------------------------------------------------------------------------------------------------------

🚀 Future Improvements

Google Fit API integration

Medication interaction checker

Doctor chat agent

Symptom analysis

User authentication

Push notifications



-----------------------------------------------------------------------------------------------

👨‍💻 Contributors
    
    Prathvika Krishna Moger 
    Chandana B
    Mrudula H N
    Pruthvi D M
    Nandini G V