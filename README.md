# IT Help Desk Ticket Management System

A web-based IT Help Desk application built using Python and Flask to manage support tickets, track issue resolution, and monitor technician performance.

## Project Overview

The IT Help Desk Ticket Management System helps organizations manage employee IT support requests through a centralized platform. Administrators and technicians can track tickets, update their status, manage priorities, and monitor service-level agreement (SLA) deadlines.

## Technologies Used

- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** SQLite
- **Charts:** Chart.js
- **Testing:** Pytest
- **Version Control:** Git

## Key Features

### 1. Authentication and Role Management
- User login and authentication
- Admin and technician roles
- Role-based access control

### 2. Ticket Management
- Create and submit support tickets
- View ticket details
- Search and filter tickets
- Update ticket status and priority
- Assign tickets to technicians
- View ticket activity history

### 3. SLA Management
- Automatic SLA deadline calculation based on ticket priority
- Track overdue tickets
- Monitor SLA performance

### 4. Dashboard and Analytics
- Total ticket statistics
- Ticket status overview
- Priority distribution charts
- Weekly ticket trends
- SLA performance insights
- Technician performance analysis
- Ticket resolution time analysis

### 5. Additional Features
- Ticket pagination
- CSV ticket export
- Responsive user interface
- Automated test coverage

## Ticket Priority and SLA

| Priority | SLA Target |
|---|---:|
| Critical | 4 hours |
| High | 8 hours |
| Medium | 24 hours |
| Low | 72 hours |

## Project Structure

```text
helpdesk-ticketing-main/
│
├── helpdesk/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── templates/
│   ├── auth.py
│   ├── db.py
│   ├── schema.sql
│   ├── seed.py
│   ├── sla.py
│   ├── tickets.py
│   └── __init__.py
│
├── tests/
├── instance/
├── sample-output/
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd helpdesk-ticketing-main
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
flask --app helpdesk run --debug
```

### 6. Open in Browser

```text
http://127.0.0.1:5000/
```

## Run Tests

Execute the following command:

```bash
pytest -v
```

## Future Enhancements

- Email notifications for ticket updates
- File attachments for support requests
- Advanced ticket reporting
- Technician workload management
- REST API integration

## Author

Developed as a Python Flask project to demonstrate web development, database management, authentication, analytics, and software testing skills.