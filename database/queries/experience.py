from database.db import get_conn


# Whitelist of columns the client is allowed to write — guards against arbitrary SQL injection
# via field names AND prevents the client from setting `id`.
EXPERIENCE_WRITABLE = (
    'company', 'title', 'location',
    'start_date', 'end_date', 'is_current',
    'summary', 'tech_stack', 'sort_order',
)


def get_user_experience():
    """Return all work_experience rows, ordered by sort_order then most recent."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, company, title, location, start_date, end_date,
                   is_current, summary, tech_stack, sort_order
            FROM work_experience
            ORDER BY sort_order ASC, is_current DESC, start_date DESC
            """
        ).fetchall()
    return [
        {
            "id":         r["id"],
            "company":    r["company"],
            "title":      r["title"],
            "location":   r["location"],
            "start_date": r["start_date"],
            "end_date":   r["end_date"],
            "is_current": r["is_current"],
            "summary":    r["summary"],
            "tech_stack": r["tech_stack"],
            "sort_order": r["sort_order"],
        }
        for r in rows
    ]


def create_user_experience(payload):
    """Insert a new experience row from a payload dict. Returns the new row id."""
    fields = {k: payload.get(k) for k in EXPERIENCE_WRITABLE if k in payload}

    # Normalize is_current
    if 'is_current' in fields:
        fields['is_current'] = 1 if int(fields['is_current'] or 0) == 1 else 0
        # If currently working, blank out end_date
        if fields['is_current'] == 1:
            fields['end_date'] = None

    if not fields:
        # Nothing to insert; create a minimal row so the client gets an id back
        with get_conn() as conn:
            cur = conn.execute("INSERT INTO work_experience DEFAULT VALUES")
            conn.commit()
            return cur.lastrowid

    cols  = ', '.join(fields.keys())
    marks = ', '.join('?' * len(fields))
    vals  = list(fields.values())

    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO work_experience ({cols}) VALUES ({marks})",
            vals,
        )
        conn.commit()
        return cur.lastrowid


def patch_user_experience(exp_id, payload):
    """Update writable fields on a single row. Returns True if the row existed."""
    fields = {k: payload.get(k) for k in EXPERIENCE_WRITABLE if k in payload}

    if 'is_current' in fields:
        fields['is_current'] = 1 if int(fields['is_current'] or 0) == 1 else 0
        if fields['is_current'] == 1:
            fields['end_date'] = None

    if not fields:
        # Nothing to change; verify the row exists so we return the right status
        with get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM work_experience WHERE id = ?", (exp_id,)
            ).fetchone()
        return row is not None

    set_clause = ', '.join(f"{k} = ?" for k in fields.keys())
    vals = list(fields.values()) + [exp_id]

    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE work_experience SET {set_clause} WHERE id = ?",
            vals,
        )
        conn.commit()
        return cur.rowcount > 0


def delete_user_experience(exp_id):
    """Delete a single row. Returns True if a row was deleted."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM work_experience WHERE id = ?", (exp_id,))
        conn.commit()
        return cur.rowcount > 0