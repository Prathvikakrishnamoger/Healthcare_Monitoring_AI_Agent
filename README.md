# 🏥 Healthcare Monitoring AI Agent

A comprehensive **Healthcare Monitoring Application** built using **Python and Streamlit** that helps users manage medications, track health records, monitor fitness activity, receive safety alerts, interact with a health chatbot, and generate downloadable health reports.

> ⚠️ **Medical Disclaimer**  
> This application is for **educational and informational purposes only**.  
> It is **NOT a substitute for professional medical advice, diagnosis, or treatment**.  
> Always consult a qualified healthcare professional for medical decisions.

---

## 📌 Project Overview

The **Healthcare Monitoring AI Agent** acts as a personal digital health assistant.  
It allows users to record and monitor their health data, manage medications safely, analyze trends, and interact with a rule-based AI chatbot for basic medical information.

The project focuses on:
- Core healthcare monitoring features
- Patient safety and data validation
- Clear visual insights
- Local database storage (no external APIs required)

---

## ✨ Key Features

### 👤 User Management
- Add and select multiple users
- Each user has isolated health and medication data

---

### 💊 Medication Management
- Add medications with:
  - Name
  - Dose
  - Time
  - Frequency
- Input validation (empty values, short names, invalid times)
- Mark medications as **taken**
- Delete medications
- Medication interaction checking using a local ruleset
- Store and display interaction alerts

#### ⏰ Medication Reminder Logic
- Each medication stores a scheduled time
- The system calculates time remaining until intake
- Visual reminders are shown when a medication is due
- Medication adherence is tracked using “Mark as taken”

> Note: No background notifications are used; reminders are logic-based and UI-driven.

---

### 🩺 Health Records
- Record:
  - Blood Pressure (BP)
  - Blood Sugar
  - Weight
- Strong input validation (e.g., BP must be `120/80`)
- Automatic detection of critical readings
- Recent health record history with timestamps
- Emergency warnings for abnormal readings

---

### 🏃 Fitness Tracking
- Log daily:
  - Steps
  - Calories
- View recent fitness logs
- Calculate averages
- Trend visualization using charts

---

### 🎯 Goals & Progress Tracking
- Create health goals (e.g., daily steps, target weight)
- Track progress using recorded data
- View progress summaries
- Delete goals when completed

---

### 📊 Health Analytics
- 7-day health analytics:
  - Average blood pressure
  - Average sugar level
  - Average steps
- Line charts for trends
- Automatic warnings for:
  - High BP
  - Very high / low sugar

---

### 💬 Health Assistant Chatbot
- Rule-based AI chatbot for health-related questions
- Accepts natural language queries
- Provides safe, non-diagnostic explanations
- Uses internal NLP utilities and medical rules

Examples:
-Commands:
            - show meds → list medications"
            - next med → next medication scheduled"
            - add med NAME;DOSE;HH:MM → add medication"
            - latest bp → show last blood pressure record"

---

### 📄 Health Report Generation
- Generate reports for a selected date range
- Includes:
  - Summary statistics
  - Charts
  - Raw data table
- Export options:
  - CSV (health records)
  - HTML (full health report)

---

## 🛠️ Technology Stack

- **Frontend:** Streamlit  
- **Backend:** Python  
- **Database:** SQLite  
- **Data Processing:** Pandas  
- **Visualization:** Matplotlib, Streamlit charts  
- **NLP:** Rule-based parsing (no external APIs)

---

## 📂 Project Structure

HEALTHCARE_MONITORING_AI_AGENT/

│

├── app.py                            # Main Streamlit application

├── chatbot.py                        # Health assistant chatbot logic

├── nlp_utils.py                      # NLP utilities

├── health_query_engine.py            # Health query processing

├── db.py                             # SQLite database operations

├── agent.py                          # Agent abstraction layer

├── drug_interactions.py              # Medication interaction rules

├── india_meds/                       # Indian medication database & helpers

├── meds_db.py                        # Medication database utilities

├── interactions.py                   # Interaction logic

├── tests/                            # Test scripts

├── requirements.txt                  # Dependencies

├── health.db                         # Main database (local)

└── README.md                         # Project documentation

🚀 How to Run the Project

    1️⃣ Clone the Repository
         git clone https://github.com/your-username/healthcare-monitoring-ai-agent.git
         cd healthcare-monitoring-ai-agent

    2️⃣ Create Virtual Environment (Recommended)
         python -m venv venv
         venv\Scripts\activate   # Windows

    3️⃣ Install Dependencies
         pip install -r requirements.txt

    4️⃣ Run the Application
         streamlit run app.py

    The app will open in your browser at: http://localhost:8501

📈 Development Summary

    * Core UI and database setup
    * Medication management with interaction checks
    * Health record validation and alerts
    * Fitness tracking and analytics
    * Chatbot integration
    * Goals, reports, exports, and UI polishing

🔐 Data & Privacy Notes

    * Uses local SQLite databases
    * No real patient data required
    * No external API calls
    * Designed for educational and prototype use

🚧 Limitations & Future Enhancements

    * SMS / push notifications for reminders
    * Authentication and role-based access
    * Cloud database support
    * Integration with fitness or health APIs
    * Voice-based chatbot interaction








