
# 🎓 EduCore - Student Management System

EduCore is a full-stack, secure, and responsive Student Management System designed to streamline academic administration, user role management, and secure communications.
## 🚀 Key Features

* **Role-Based Access Control (RBAC):** Distinct dashboards and security perimeters for Administrators, Teachers, and Students.
* **Automated Gmail SMTP Credential Delivery:** Instantly generates secure passwords and dispatches automated login credentials to registered users via SMTP (`rahmimuhe6@gmail.com`).
* **Self-Service Password Recovery:** Secure recovery workflow backed by cryptographic hashing.
* **Department-Based Filtering & Search:** Easily sort, filter, and manage student and faculty directories.
* **Student Photo Uploads:** Profile picture management integrated into student profiles.
* **Secure Authentication:** Password hashing powered by SHA-256 and data validation enforced via Pydantic.
## 🛠️ Technology Stack
* **Frontend:** HTML5, Modern JavaScript, Tailwind CSS (CDN-driven UI).
* **Backend:** Python 3.13, FastAPI, Uvicorn ASGI Server.
* **Database & Validation:** SQLite, Pydantic, SQL-backed relational mapping.
## 📂 Project Directory Structure
text
Student_Management_System/
├── backend/
│   ├── main.py              # FastAPI application entry point, routes, and auth logic
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── index.html           # Landing & Home interface
│   ├── portal.html          # Unified login and role portals
│   ├── about.html           # System overview page
│   └── app.js               # Frontend API integration & dynamic DOM rendering
├── students.db              # Local SQLite database instance
└── README.md                # Project documentation
⚙️ Getting Started & Local Installation
1. Clone the Repository
Bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd Student_Management_System
2. Install Backend Dependencies
Make sure you are in the root directory, then run:

Bash
pip install -r backend/requirements.txt
3. Run the FastAPI Backend Server
Start the Uvicorn server using Python module execution:

Bash
python -m uvicorn backend.main:app --reload
The API server will run live at http://127.0.0.1:8000.

4. Launch the Frontend
Open frontend/index.html using VS Code Live Server or any static local server to interact with the UI.

🛡️ License
This project is open-source and developed for educational and administrative management purposes.
