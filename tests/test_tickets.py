
from helpdesk.db import get_db


def create_test_ticket(client):
    return client.post(
        "/tickets/new",
        data={
            "requester_name": "Rahul",
            "requester_email": "rahul@example.com",
            "title": "Laptop is not starting",
            "description": "My laptop does not power on.",
            "category": "Hardware",
            "priority": "High",
        },
        follow_redirects=True,
    )


def create_multiple_tickets(client, count):
    """Create multiple tickets for pagination testing."""

    for number in range(1, count + 1):
        client.post(
            "/tickets/new",
            data={
                "requester_name": "Pagination Tester",
                "requester_email": "pagination@example.com",
                "title": f"Pagination Ticket {number:02d}",
                "description": f"Test ticket number {number}.",
                "category": "Hardware",
                "priority": "Medium",
            },
            follow_redirects=True,
        )


# --------------------------------------------------
# TICKET CREATION TESTS
# --------------------------------------------------

def test_ticket_creation(logged_in_client):
    response = create_test_ticket(logged_in_client)

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


def test_ticket_creation_with_invalid_email(logged_in_client):
    response = logged_in_client.post(
        "/tickets/new",
        data={
            "requester_name": "Rahul",
            "requester_email": "invalid-email",
            "title": "Laptop issue",
            "description": "Laptop is not working.",
            "category": "Hardware",
            "priority": "High",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please enter a valid email address." in response.data


def test_ticket_creation_with_missing_fields(logged_in_client):
    response = logged_in_client.post(
        "/tickets/new",
        data={
            "requester_name": "Rahul",
            "requester_email": "rahul@example.com",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please fill in all required fields." in response.data


# --------------------------------------------------
# TICKET LIST AND DETAIL TESTS
# --------------------------------------------------

def test_ticket_list_loads(logged_in_client):
    response = logged_in_client.get("/tickets")

    assert response.status_code == 200


def test_ticket_detail_loads(logged_in_client, app):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()
        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        ticket_id = ticket["id"]

    response = logged_in_client.get(f"/tickets/{ticket_id}")

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


def test_nonexistent_ticket_returns_404(logged_in_client):
    response = logged_in_client.get("/tickets/99999")

    assert response.status_code == 404


# --------------------------------------------------
# TICKET UPDATE TESTS
# --------------------------------------------------

def test_ticket_status_update(logged_in_client, app):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()
        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        ticket_id = ticket["id"]

    response = logged_in_client.post(
        f"/tickets/{ticket_id}/update",
        data={
            "status": "In Progress",
            "priority": "High",
            "assigned_to": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        database = get_db()
        updated_ticket = database.execute(
            "SELECT status FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        assert updated_ticket["status"] == "In Progress"


def test_invalid_ticket_status_is_rejected(logged_in_client, app):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()
        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        ticket_id = ticket["id"]

    logged_in_client.post(
        f"/tickets/{ticket_id}/update",
        data={
            "status": "Invalid Status",
            "priority": "High",
            "assigned_to": "",
        },
    )

    with app.app_context():
        database = get_db()
        updated_ticket = database.execute(
            "SELECT status FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        assert updated_ticket["status"] == "Open"


def test_admin_can_assign_ticket_to_technician(logged_in_client, app):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()

        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        technician = database.execute(
            "SELECT id FROM users WHERE username = 'technician'"
        ).fetchone()

        ticket_id = ticket["id"]
        technician_id = technician["id"]

    response = logged_in_client.post(
        f"/tickets/{ticket_id}/update",
        data={
            "status": "Open",
            "priority": "High",
            "assigned_to": str(technician_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        database = get_db()

        updated = database.execute(
            "SELECT assigned_to FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        assert updated["assigned_to"] == technician_id


def test_invalid_technician_assignment_is_rejected(
    logged_in_client, app
):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()

        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        ticket_id = ticket["id"]

    logged_in_client.post(
        f"/tickets/{ticket_id}/update",
        data={
            "status": "Open",
            "priority": "High",
            "assigned_to": "99999",
        },
    )

    with app.app_context():
        database = get_db()

        updated = database.execute(
            "SELECT assigned_to FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        assert updated["assigned_to"] is None


def test_invalid_assignment_format_is_rejected(
    logged_in_client, app
):
    create_test_ticket(logged_in_client)

    with app.app_context():
        database = get_db()

        ticket = database.execute(
            "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
        ).fetchone()

        ticket_id = ticket["id"]

    logged_in_client.post(
        f"/tickets/{ticket_id}/update",
        data={
            "status": "Open",
            "priority": "High",
            "assigned_to": "invalid",
        },
    )

    with app.app_context():
        database = get_db()

        updated = database.execute(
            "SELECT assigned_to FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        assert updated["assigned_to"] is None


# --------------------------------------------------
# SEARCH AND FILTER TESTS
# --------------------------------------------------

def test_ticket_search_by_title(logged_in_client):
    create_test_ticket(logged_in_client)

    response = logged_in_client.get("/tickets?q=Laptop")

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


def test_ticket_search_no_results(logged_in_client):
    response = logged_in_client.get(
        "/tickets?q=NonexistentTicket123"
    )

    assert response.status_code == 200
    assert b"Laptop is not starting" not in response.data


def test_ticket_filter_by_status(logged_in_client):
    create_test_ticket(logged_in_client)

    response = logged_in_client.get("/tickets?status=Open")

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


def test_ticket_filter_by_priority(logged_in_client):
    create_test_ticket(logged_in_client)

    response = logged_in_client.get("/tickets?priority=High")

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


def test_ticket_filter_by_category(logged_in_client):
    create_test_ticket(logged_in_client)

    response = logged_in_client.get("/tickets?category=Hardware")

    assert response.status_code == 200
    assert b"Laptop is not starting" in response.data


# --------------------------------------------------
# PAGINATION TESTS
# --------------------------------------------------

def test_ticket_pagination_first_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get("/tickets?page=1")

    assert response.status_code == 200
    assert b"Pagination Ticket 12" in response.data
    assert b"Pagination Ticket 03" in response.data
    assert b"Pagination Ticket 02" not in response.data
    assert b"Pagination Ticket 01" not in response.data


def test_ticket_pagination_second_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get("/tickets?page=2")

    assert response.status_code == 200
    assert b"Pagination Ticket 02" in response.data
    assert b"Pagination Ticket 01" in response.data
    assert b"Pagination Ticket 03" not in response.data
    assert b"Pagination Ticket 12" not in response.data


def test_invalid_pagination_page_defaults_to_first(
    logged_in_client
):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get("/tickets?page=invalid")

    assert response.status_code == 200
    assert b"Pagination Ticket 12" in response.data
    assert b"Pagination Ticket 03" in response.data
    assert b"Pagination Ticket 02" not in response.data


def test_pagination_page_beyond_last_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get("/tickets?page=999")

    assert response.status_code == 200
    assert b"Pagination Ticket 02" in response.data
    assert b"Pagination Ticket 01" in response.data
    assert b"Pagination Ticket 03" not in response.data


# --------------------------------------------------
# PAGINATION EDGE-CASE TESTS
# --------------------------------------------------

def test_empty_ticket_list_loads(logged_in_client):
    response = logged_in_client.get("/tickets")

    assert response.status_code == 200


def test_exactly_ten_tickets_fit_on_one_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 10)

    response = logged_in_client.get("/tickets?page=1")

    assert response.status_code == 200

    assert b"Pagination Ticket 10" in response.data
    assert b"Pagination Ticket 01" in response.data


def test_negative_pagination_page_defaults_to_first(
    logged_in_client
):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get("/tickets?page=-5")

    assert response.status_code == 200

    assert b"Pagination Ticket 12" in response.data
    assert b"Pagination Ticket 03" in response.data
    assert b"Pagination Ticket 02" not in response.data


def test_search_works_with_second_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get(
        "/tickets?q=Pagination&page=2"
    )

    assert response.status_code == 200

    assert b"Pagination Ticket 02" in response.data
    assert b"Pagination Ticket 01" in response.data
    assert b"Pagination Ticket 03" not in response.data


def test_status_filter_works_with_second_page(logged_in_client):
    create_multiple_tickets(logged_in_client, 12)

    response = logged_in_client.get(
        "/tickets?status=Open&page=2"
    )

    assert response.status_code == 200

    assert b"Pagination Ticket 02" in response.data
    assert b"Pagination Ticket 01" in response.data
    assert b"Pagination Ticket 03" not in response.data
