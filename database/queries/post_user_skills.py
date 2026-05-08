from database.db import get_conn

def add_user_skills(skills: list[str]) -> int:
    """Replace all rows in the skills table with the given list of names.
    Returns the number of skills inserted."""
    with get_conn() as conn:
        conn.execute("DELETE FROM skills")
        conn.executemany(
            "INSERT INTO skills (name) VALUES (?)",
            [(name,) for name in skills],
        )
        conn.commit()
    return len(skills)