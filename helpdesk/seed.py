
from datetime import timedelta

from werkzeug.security import generate_password_hash

from .db import get_db
from .sla import calculate_due_date, utc_now


def seed_demo():
    database = get_db()

    users = [
        ("rahul", "Rahul Sharma", "rahul@example.com", "admin"),
        ("priya", "Priya Reddy", "priya@example.com", "technician"),
        ("arjun", "Arjun Kumar", "arjun@example.com", "technician"),
    ]

    for username, name, email, role in users:
        database.execute(
            """
            INSERT OR IGNORE INTO users
            (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                generate_password_hash("Helpdesk@2026"),
                name,
                email,
                role,
            ),
        )

    database.commit()

    if database.execute(
        "SELECT COUNT(*) FROM tickets"
    ).fetchone()[0] > 0:
        print("Sample tickets already exist. Skipping ticket creation.")
        return

    technicians = database.execute(
        """
        SELECT id FROM users
        WHERE role = 'technician'
        ORDER BY username
        """
    ).fetchall()

    priya_id = technicians[0]["id"]
    arjun_id = technicians[1]["id"]

    samples = [
        (
            "Ananya Rao", "ananya@example.com",
            "Laptop not starting", "Laptop does not power on after pressing the power button.",
            "Hardware", "Critical", None,
        ),
        (
            "Kiran Kumar", "kiran@example.com",
            "Printer on first floor jams", "The printer repeatedly jams while printing documents.",
            "Printer", "High", priya_id,
        ),
        (
            "Sneha Reddy", "sneha@example.com",
            "Unable to access company email", "Email login fails with an authentication error.",
            "Email", "Medium", arjun_id,
        ),
        (
            "Rahul Verma", "rahulv@example.com",
            "Wi-Fi connection is unstable", "Office Wi-Fi disconnects frequently.",
            "Network", "High", priya_id,
        ),
        (
            "Meena Sharma", "meena@example.com",
            "Software installation request", "Need installation of approved office software.",
            "Software", "Low", arjun_id,
        ),
        (
            "Vikram Rao", "vikram@example.com",
            "Account locked", "Unable to sign in after multiple login attempts.",
            "Account Access", "Critical", priya_id,
        ),
        (
            "Divya Patel", "divya@example.com",
            "Monitor display flickering", "External monitor flickers intermittently.",
            "Hardware", "Medium", None,
        ),
        (
            "Suresh Kumar", "suresh@example.com",
            "VPN connection problem", "VPN connection fails from home network.",
            "Network", "High", arjun_id,
        ),
        (
            "Priya Nair", "priyan@example.com",
            "Keyboard keys not working", "Several keyboard keys are unresponsive.",
            "Hardware", "Low", None,
        ),
    ]

    now = utc_now()

    for index, sample in enumerate(samples):
        (
            name, email, title, description,
            category, priority, assigned_to,
        ) = sample

        created_at = now - timedelta(hours=index * 3)
        due_at = calculate_due_date(priority, created_at)

        cursor = database.execute(
            """
            INSERT INTO tickets (
                requester_name, requester_email,
                title, description, category,
                priority, status, assigned_to,
                due_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name, email, title, description,
                category, priority, "Open", assigned_to,
                due_at, created_at.isoformat(),
                created_at.isoformat(),
            ),
        )

        database.execute(
            """
            INSERT INTO ticket_history
            (ticket_id, user_id, action, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cursor.lastrowid,
                None,
                "Created",
                "Sample support ticket created.",
                created_at.isoformat(),
            ),
        )

    database.commit()

    print("Demo users and sample tickets created successfully.")
    print("Usernames: rahul, priya, arjun")
    print("Password: Helpdesk@2026")
