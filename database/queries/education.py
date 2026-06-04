from database.db import get_conn


# Whitelist of columns the client may write — blocks arbitrary field names and `id`.
EDUCATION_WRITABLE = (
    'school', 'program', 'degree_type', 'gpa',
    'start_date', 'end_date', 'currently_enrolled',
    'summary', 'sort_order',
)


def get_user_education():
    """Return all education rows, ordered by sort_order then most recent."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, school, program, degree_type, gpa,
                   start_date, end_date, currently_enrolled, summary, sort_order
            FROM education
            ORDER BY sort_order ASC, currently_enrolled DESC, start_date DESC
            """
        ).fetchall()
    return [
        {
            "id":                 r["id"],
            "school":             r["school"],
            "program":            r["program"],
            "degree_type":        r["degree_type"],
            "gpa":                r["gpa"],
            "start_date":         r["start_date"],
            "end_date":           r["end_date"],
            "currently_enrolled": r["currently_enrolled"],
            "summary":            r["summary"],
            "sort_order":         r["sort_order"],
        }
        for r in rows
    ]


def create_user_education(payload):
    """Insert a new education row from a payload dict. Returns the new row id."""
    fields = {k: payload.get(k) for k in EDUCATION_WRITABLE if k in payload}

    # Normalize the bool. (Note: we KEEP end_date even when enrolled — it's the
    # expected graduation year, unlike work_experience which blanks it.)
    if 'currently_enrolled' in fields:
        fields['currently_enrolled'] = 1 if int(fields['currently_enrolled'] or 0) == 1 else 0

    if not fields:
        with get_conn() as conn:
            cur = conn.execute("INSERT INTO education DEFAULT VALUES")
            conn.commit()
            return cur.lastrowid

    cols  = ', '.join(fields.keys())
    marks = ', '.join('?' * len(fields))
    vals  = list(fields.values())

    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO education ({cols}) VALUES ({marks})",
            vals,
        )
        conn.commit()
        return cur.lastrowid


def patch_user_education(edu_id, payload):
    """Update writable fields on a single row. Returns True if the row existed."""
    fields = {k: payload.get(k) for k in EDUCATION_WRITABLE if k in payload}

    if 'currently_enrolled' in fields:
        fields['currently_enrolled'] = 1 if int(fields['currently_enrolled'] or 0) == 1 else 0

    if not fields:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM education WHERE id = ?", (edu_id,)
            ).fetchone()
        return row is not None

    set_clause = ', '.join(f"{k} = ?" for k in fields.keys())
    vals = list(fields.values()) + [edu_id]

    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE education SET {set_clause} WHERE id = ?",
            vals,
        )
        conn.commit()
        return cur.rowcount > 0


def delete_user_education(edu_id):
    """Delete a single row. Returns True if a row was deleted."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM education WHERE id = ?", (edu_id,))
        conn.commit()
        return cur.rowcount > 0