
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
