
import json
from database.db import get_conn

def get_user_skils():
    """Return all skills from skill_catalog as a list of {name, category} dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT name FROM skills ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]