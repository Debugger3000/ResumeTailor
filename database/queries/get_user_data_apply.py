import json
from database.db import get_conn

def get_user_profile() -> dict:
    """Fetch the single user_profile row as a flat dict."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    if not row:
        return {}
    profile = dict(row)
    profile.pop("id", None)
    profile.pop("updated_at", None)
    return profile


def get_work_experience() -> list[dict]:
    """Fetch all work experience entries, parsed."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM work_experience ORDER BY sort_order, id"
        ).fetchall()

    result = []
    for row in rows:
        entry = dict(row)
        # Parse JSON tech_stack back into a list
        if entry.get("tech_stack"):
            try:
                entry["tech_stack"] = json.loads(entry["tech_stack"])
            except json.JSONDecodeError:
                entry["tech_stack"] = []
        else:
            entry["tech_stack"] = []
        entry.pop("sort_order", None)
        result.append(entry)
    return result


def get_user_skills() -> list[str]:
    """Fetch user skills as a flat list of names."""
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM skills ORDER BY name").fetchall()
    return [r["name"] for r in rows]