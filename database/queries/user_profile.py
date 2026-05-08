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
    print(profile)
    return profile


def update_user_profile(fields: dict) -> None:
    """Upsert the single user_profile row with the given fields.
    Only updates columns that exist in the table; ignores extras."""
    if not fields:
        return

    # Whitelist against actual column names to prevent SQL injection
    # via field names and silently drop anything bogus
    with get_conn() as conn:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(user_profile)").fetchall()}
        cols.discard("id")
        cols.discard("updated_at")

        valid = {k: v for k, v in fields.items() if k in cols}
        if not valid:
            return

        keys = list(valid.keys())
        values = [valid[k] for k in keys]

        # INSERT OR REPLACE the single row, but only for provided fields.
        # Use ON CONFLICT to do an UPSERT that preserves untouched columns.
        placeholders = ", ".join("?" for _ in keys)
        col_list = ", ".join(keys)
        update_set = ", ".join(f"{k} = excluded.{k}" for k in keys)

        sql = f"""
            INSERT INTO user_profile (id, {col_list})
            VALUES (1, {placeholders})
            ON CONFLICT(id) DO UPDATE SET
                {update_set},
                updated_at = CURRENT_TIMESTAMP
        """
        conn.execute(sql, values)
        conn.commit()