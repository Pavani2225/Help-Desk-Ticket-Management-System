
import csv
import io
import re
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint, Response, abort, flash, g, redirect,
    render_template, request, url_for
)

from .auth import login_required
from .db import get_db
from .sla import calculate_due_date, utc_now

bp = Blueprint("tickets", __name__)


def add_history(ticket_id, action, details=""):
    database = get_db()

    database.execute(
        """
        INSERT INTO ticket_history
        (ticket_id, user_id, action, details)
        VALUES (?, ?, ?, ?)
        """,
        (ticket_id, g.user["id"], action, details)
    )


def get_ticket(ticket_id):
    ticket = get_db().execute(
        """
        SELECT t.*, u.full_name AS assigned_name
        FROM tickets t
        LEFT JOIN users u ON t.assigned_to = u.id
        WHERE t.id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:
        abort(404)

    return ticket


def parse_timestamp(value):
    """Convert a stored timestamp into a timezone-aware datetime."""
    if not value:
        return None

    try:
        result = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result.astimezone(timezone.utc)

    except (ValueError, TypeError):
        return None


def format_duration(total_seconds):
    """Display a duration in days, hours and minutes."""
    total_minutes = max(0, int(total_seconds // 60))

    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60

    if days:
        return f"{days}d {hours}h"

    if hours:
        return f"{hours}h {minutes}m"

    if minutes:
        return f"{minutes}m"

    return "Less than 1m"


def get_resolution_stats(database):
    """Calculate resolution times using actual ticket history."""

    completed_count = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status IN ('Resolved', 'Closed')
        """
    ).fetchone()["total"]

    resolution_rows = database.execute(
        """
        SELECT
            t.id,
            t.created_at,
            (
                SELECT MAX(h.created_at)
                FROM ticket_history AS h
                WHERE h.ticket_id = t.id
                AND h.action = 'Status changed'
                AND (
                    h.details LIKE '%→ Resolved'
                    OR h.details LIKE '%→ Closed'
                )
            ) AS resolved_at
        FROM tickets AS t
        WHERE t.status IN ('Resolved', 'Closed')
        """
    ).fetchall()

    durations = []

    for row in resolution_rows:
        created_at = parse_timestamp(row["created_at"])
        resolved_at = parse_timestamp(row["resolved_at"])

        if not created_at or not resolved_at:
            continue

        seconds = (resolved_at - created_at).total_seconds()

        if seconds >= 0:
            durations.append(seconds)

    if not durations:
        return {
            "average_time": "No data yet",
            "fastest_time": "No data yet",
            "longest_time": "No data yet",
            "completed": completed_count,
        }

    return {
        "average_time": format_duration(
            sum(durations) / len(durations)
        ),
        "fastest_time": format_duration(min(durations)),
        "longest_time": format_duration(max(durations)),
        "completed": completed_count,
    }


def get_technician_stats(database):
    """Calculate ticket workload and resolution performance per technician."""

    rows = database.execute(
        """
        SELECT
            u.id,
            u.full_name,
            COUNT(t.id) AS total_assigned,

            SUM(
                CASE
                    WHEN t.status IN ('Resolved', 'Closed') THEN 1
                    ELSE 0
                END
            ) AS resolved_tickets,

            SUM(
                CASE
                    WHEN t.status IN ('Open', 'In Progress') THEN 1
                    ELSE 0
                END
            ) AS open_tickets

        FROM users AS u

        LEFT JOIN tickets AS t
            ON t.assigned_to = u.id

        WHERE u.role = 'technician'
        AND u.is_active = 1

        GROUP BY u.id, u.full_name

        ORDER BY total_assigned DESC, u.full_name ASC
        """
    ).fetchall()

    technicians = []

    for row in rows:
        total = row["total_assigned"] or 0
        resolved = row["resolved_tickets"] or 0
        open_count = row["open_tickets"] or 0

        resolution_rate = round(
            resolved * 100 / total
        ) if total else 0

        technicians.append({
            "id": row["id"],
            "name": row["full_name"],
            "total_assigned": total,
            "resolved": resolved,
            "open": open_count,
            "resolution_rate": resolution_rate,
        })

    return technicians


@bp.route("/")
@login_required
def dashboard():
    database = get_db()

    # Weekly ticket activity
    today = utc_now().date()
    start_date = (today - timedelta(days=6)).isoformat()

    created_rows = database.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS total
        FROM tickets
        WHERE date(created_at) >= ?
        GROUP BY date(created_at)
        """,
        (start_date,)
    ).fetchall()

    resolved_rows = database.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS total
        FROM ticket_history
        WHERE action = 'Status changed'
        AND (
            details LIKE '%→ Resolved'
            OR details LIKE '%→ Closed'
        )
        AND date(created_at) >= ?
        GROUP BY date(created_at)
        """,
        (start_date,)
    ).fetchall()

    created_by_day = {
        row["day"]: row["total"]
        for row in created_rows
    }

    resolved_by_day = {
        row["day"]: row["total"]
        for row in resolved_rows
    }

    weekly_labels = []
    weekly_created = []
    weekly_resolved = []

    for offset in range(6, -1, -1):
        current_day = today - timedelta(days=offset)
        day_key = current_day.isoformat()

        weekly_labels.append(current_day.strftime("%a"))
        weekly_created.append(created_by_day.get(day_key, 0))
        weekly_resolved.append(resolved_by_day.get(day_key, 0))

    # Ticket status statistics
    by_status = {
        row["status"]: row["total"]
        for row in database.execute(
            """
            SELECT status, COUNT(*) AS total
            FROM tickets
            GROUP BY status
            """
        ).fetchall()
    }

    for status in ("Open", "In Progress", "Resolved", "Closed"):
        by_status.setdefault(status, 0)

    # Ticket priority statistics
    by_priority = {
        row["priority"]: row["total"]
        for row in database.execute(
            """
            SELECT priority, COUNT(*) AS total
            FROM tickets
            WHERE status IN ('Open', 'In Progress')
            GROUP BY priority
            """
        ).fetchall()
    }

    for priority in ("Critical", "High", "Medium", "Low"):
        by_priority.setdefault(priority, 0)

    # Overdue tickets
    overdue = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status IN ('Open', 'In Progress')
        AND datetime(due_at) < datetime(?)
        """,
        (utc_now().isoformat(),)
    ).fetchone()["total"]

    # Unassigned tickets
    unassigned = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status IN ('Open', 'In Progress')
        AND assigned_to IS NULL
        """
    ).fetchone()["total"]

    # Tickets assigned to current user
    mine = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status IN ('Open', 'In Progress')
        AND assigned_to = ?
        """,
        (g.user["id"],)
    ).fetchone()["total"]

    # Total tickets
    total = database.execute(
        "SELECT COUNT(*) AS total FROM tickets"
    ).fetchone()["total"]

    # Total completed tickets
    resolved_total = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status IN ('Resolved', 'Closed')
        """
    ).fetchone()["total"]

    # Tickets resolved within their SLA deadline
    resolved_on_time = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM tickets AS t
        WHERE t.status IN ('Resolved', 'Closed')

        AND EXISTS (
            SELECT 1
            FROM ticket_history AS h
            WHERE h.ticket_id = t.id
            AND h.action = 'Status changed'
            AND (
                h.details LIKE '%→ Resolved'
                OR h.details LIKE '%→ Closed'
            )
            AND datetime(h.created_at) <= datetime(t.due_at)

            AND h.created_at = (
                SELECT MAX(h2.created_at)
                FROM ticket_history AS h2
                WHERE h2.ticket_id = t.id
                AND h2.action = 'Status changed'
            )
        )
        """
    ).fetchone()["total"]

    sla_rate = round(
        resolved_on_time * 100 / max(1, resolved_total)
    )

    # Ticket resolution time analysis
    resolution_stats = get_resolution_stats(database)

    # Technician performance analysis
    technician_stats = get_technician_stats(database)

    # Most urgent tickets
    urgent = database.execute(
        """
        SELECT *
        FROM tickets
        WHERE status IN ('Open', 'In Progress')
        ORDER BY
            CASE priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            due_at ASC
        LIMIT 5
        """
    ).fetchall()

    stats = {
        "overdue": overdue,
        "unassigned": unassigned,
        "mine": mine,
        "total": total,
        "sla_rate": sla_rate,
    }

    return render_template(
        "dashboard.html",
        by_status=by_status,
        by_priority=by_priority,
        stats=stats,
        urgent=urgent,
        weekly_labels=weekly_labels,
        weekly_created=weekly_created,
        weekly_resolved=weekly_resolved,
        resolution_stats=resolution_stats,
        technician_stats=technician_stats,
    )


@bp.route("/tickets")
@login_required
def list_tickets():
    database = get_db()

    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    assigned = request.args.get("assigned", "").strip()
    overdue = request.args.get("overdue", "").strip()

    # Pagination settings
    per_page = 10

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    conditions = []
    params = []

    if status == "active":
        conditions.append(
            "t.status IN ('Open', 'In Progress')"
        )
    elif status:
        conditions.append("t.status = ?")
        params.append(status)

    if priority:
        conditions.append("t.priority = ?")
        params.append(priority)

    if category:
        conditions.append("t.category = ?")
        params.append(category)

    # Search tickets by title, description, requester or ticket ID
    if search:
        id_match = re.search(r"(\d+)$", search)
        ticket_id = int(id_match.group(1)) if id_match else -1

        conditions.append(
            """
            (
                t.title LIKE ? OR t.description LIKE ?
                OR t.requester_name LIKE ?
                OR t.requester_email LIKE ?
                OR CAST(t.id AS TEXT) LIKE ?
                OR t.id = ?
            )
            """
        )

        pattern = f"%{search}%"

        params.extend([
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
            ticket_id,
        ])

    # Assignment filters
    if assigned == "none":
        conditions.append("t.assigned_to IS NULL")

    elif assigned == "me":
        conditions.append("t.assigned_to = ?")
        params.append(g.user["id"])

    # Overdue filter
    if overdue == "1":
        conditions.append(
            """
            t.status IN ('Open', 'In Progress')
            AND t.due_at < ?
            """
        )
        params.append(utc_now().isoformat())

    where = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    # Count matching tickets
    total_tickets = database.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM tickets AS t
        {where}
        """,
        params
    ).fetchone()["total"]

    # Calculate pagination
    total_pages = max(
        1,
        (total_tickets + per_page - 1) // per_page
    )

    page = min(page, total_pages)
    offset = (page - 1) * per_page

    # Fetch current page
    tickets = database.execute(
        f"""
        SELECT t.*, u.full_name AS assigned_name
        FROM tickets AS t
        LEFT JOIN users AS u
            ON t.assigned_to = u.id
        {where}
        ORDER BY t.created_at DESC, t.id DESC
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset]
    ).fetchall()

    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page=page,
        total_pages=total_pages,
        total_tickets=total_tickets,
        filters={
            "status": status,
            "priority": priority,
            "category": category,
            "q": search,
            "assigned": assigned,
            "overdue": overdue,
        }
    )


# --------------------------------------------------
# EXPORT TICKETS TO CSV
# --------------------------------------------------

@bp.route("/tickets/export")
@login_required
def export_tickets():
    # Only administrators can export tickets.
    if g.user["role"] != "admin":
        abort(403)

    database = get_db()

    tickets = database.execute(
        """
        SELECT
            t.id,
            t.title,
            t.requester_name,
            t.requester_email,
            t.category,
            t.priority,
            t.status,
            u.full_name AS assigned_technician,
            t.created_at,
            t.due_at
        FROM tickets AS t
        LEFT JOIN users AS u
            ON t.assigned_to = u.id
        ORDER BY t.created_at DESC, t.id DESC
        """
    ).fetchall()

    output = io.StringIO(newline="")
    output.write("\ufeff")

    writer = csv.writer(output)

    writer.writerow([
        "Ticket ID",
        "Title",
        "Requester Name",
        "Requester Email",
        "Category",
        "Priority",
        "Status",
        "Assigned Technician",
        "Created At",
        "SLA Deadline",
    ])

    for ticket in tickets:
        row = [
            ticket["id"],
            ticket["title"],
            ticket["requester_name"],
            ticket["requester_email"],
            ticket["category"],
            ticket["priority"],
            ticket["status"],
            ticket["assigned_technician"] or "Unassigned",
            ticket["created_at"],
            ticket["due_at"],
        ]

        safe_row = []

        for value in row:
            value = "" if value is None else str(value)

            # Protect spreadsheet users from CSV formula injection.
            if value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value

            safe_row.append(value)

        writer.writerow(safe_row)

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="helpdesk_tickets.csv"'
        },
    )


@bp.route("/tickets/new", methods=("GET", "POST"))
@login_required
def new_ticket():
    if request.method == "POST":
        name = request.form.get("requester_name", "").strip()
        email = request.form.get("requester_email", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        priority = request.form.get("priority", "Medium").strip()

        error = None

        if not all([name, email, title, description, category]):
            error = "Please fill in all required fields."

        elif not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email
        ):
            error = "Please enter a valid email address."

        elif priority not in (
            "Critical", "High", "Medium", "Low"
        ):
            error = "Please select a valid priority."

        if error:
            flash(error, "error")

        else:
            database = get_db()

            cursor = database.execute(
                """
                INSERT INTO tickets (
                    requester_name, requester_email,
                    title, description, category,
                    priority, status, due_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Open', ?)
                """,
                (
                    name,
                    email,
                    title,
                    description,
                    category,
                    priority,
                    calculate_due_date(priority),
                )
            )

            ticket_id = cursor.lastrowid

            add_history(
                ticket_id,
                "Created",
                "Ticket submitted."
            )

            database.commit()

            return redirect(
                url_for(
                    "tickets.submitted",
                    ticket_id=ticket_id
                )
            )

    return render_template("tickets/new.html")


@bp.route("/tickets/submitted/<int:ticket_id>")
@login_required
def submitted(ticket_id):
    ticket = get_ticket(ticket_id)

    return render_template(
        "tickets/submitted.html",
        ticket=ticket
    )


@bp.route("/tickets/<int:ticket_id>")
@login_required
def detail(ticket_id):
    database = get_db()
    ticket = get_ticket(ticket_id)

    history = database.execute(
        """
        SELECT h.*, u.full_name AS user_name
        FROM ticket_history AS h
        LEFT JOIN users AS u ON h.user_id = u.id
        WHERE h.ticket_id = ?
        ORDER BY h.created_at DESC
        """,
        (ticket_id,)
    ).fetchall()

    users = database.execute(
        """
        SELECT id, full_name
        FROM users
        WHERE is_active = 1
        ORDER BY full_name
        """
    ).fetchall()

    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        history=history,
        users=users
    )


@bp.route("/tickets/<int:ticket_id>/update", methods=("POST",))
@login_required
def update(ticket_id):
    database = get_db()
    ticket = get_ticket(ticket_id)

    status = request.form.get(
        "status", ticket["status"]
    )

    priority = request.form.get(
        "priority", ticket["priority"]
    )

    assigned_to = request.form.get(
        "assigned_to", ""
    ).strip()

    valid_statuses = (
        "Open", "In Progress", "Resolved", "Closed"
    )

    valid_priorities = (
        "Critical", "High", "Medium", "Low"
    )

    if (
        status not in valid_statuses
        or priority not in valid_priorities
    ):
        flash(
            "Invalid status or priority.",
            "error"
        )

        return redirect(
            url_for(
                "tickets.detail",
                ticket_id=ticket_id
            )
        )

    if assigned_to and not assigned_to.isdigit():
        flash(
            "Invalid technician selection.",
            "error"
        )

        return redirect(
            url_for(
                "tickets.detail",
                ticket_id=ticket_id
            )
        )

    assigned_id = (
        int(assigned_to)
        if assigned_to else None
    )

    if assigned_id is not None:
        user = database.execute(
            """
            SELECT id
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (assigned_id,)
        ).fetchone()

        if user is None:
            flash(
                "Selected technician does not exist.",
                "error"
            )

            return redirect(
                url_for(
                    "tickets.detail",
                    ticket_id=ticket_id
                )
            )

    if (
        g.user["role"] != "admin"
        and assigned_id != ticket["assigned_to"]
    ):
        flash(
            "Only administrators can reassign tickets.",
            "error"
        )

        return redirect(
            url_for(
                "tickets.detail",
                ticket_id=ticket_id
            )
        )

    if status != ticket["status"]:
        add_history(
            ticket_id,
            "Status changed",
            f"{ticket['status']} → {status}"
        )

    if priority != ticket["priority"]:
        add_history(
            ticket_id,
            "Priority changed",
            f"{ticket['priority']} → {priority}"
        )

    if assigned_id != ticket["assigned_to"]:
        add_history(
            ticket_id,
            "Assignment changed",
            f"Assigned user ID: {assigned_id or 'Unassigned'}"
        )

    database.execute(
        """
        UPDATE tickets
        SET status = ?,
            priority = ?,
            assigned_to = ?,
            due_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            priority,
            assigned_id,
            calculate_due_date(priority)
                if priority != ticket["priority"]
                else ticket["due_at"],
            utc_now().isoformat(),
            ticket_id,
        )
    )

    database.commit()

    flash(
        "Ticket updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "tickets.detail",
            ticket_id=ticket_id
        )
    )
