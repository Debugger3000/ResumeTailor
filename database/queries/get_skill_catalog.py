from database.db import get_conn

def get_skills_catalog():
    """Return all skills from skill_catalog as a list of {name, category} dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT name, category FROM skill_catalog ORDER BY category, name"
        ).fetchall()
    return [{"name": r["name"], "category": r["category"]} for r in rows]