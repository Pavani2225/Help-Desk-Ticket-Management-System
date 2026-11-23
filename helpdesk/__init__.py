
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask

from . import db, sla


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY", "change-this-development-secret"
        ),
        DATABASE=os.path.join(
            app.instance_path, "helpdesk.sqlite"
        ),
        DISPLAY_TIMEZONE="Asia/Kolkata",
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from . import auth, tickets, seed

    app.register_blueprint(auth.bp)
    app.register_blueprint(tickets.bp)

    @app.cli.command("seed-demo")
    def seed_demo_command():
        seed.seed_demo()

    @app.template_filter("localtime")
    def localtime_filter(value):
        if not value:
            return "-"

        try:
            date = datetime.fromisoformat(value)

            if date.tzinfo is None:
                from datetime import timezone
                date = date.replace(tzinfo=timezone.utc)

            date = date.astimezone(
                ZoneInfo(app.config["DISPLAY_TIMEZONE"])
            )

            return date.strftime("%d %b %Y %H:%M")
        except (ValueError, TypeError):
            return value

    @app.context_processor
    def utility_functions():
        return {
            "ticket_ref": lambda ticket_id: f"INC-{ticket_id:04d}",
            "is_overdue": sla.is_overdue,
            "time_left": sla.time_left,
        }

    return app
