
from database.db import get_conn


def save_model_config(provider, model_name, host=None, api_key_env=None):
    """Replace the single model_config row with the given values."""
    with get_conn() as conn:        # adjust to whatever your connection helper is
        conn.execute("DELETE FROM model_config")
        conn.execute(
            """
            INSERT INTO model_config (id, provider, model_name, api_key_env, host)
            VALUES (1, ?, ?, ?, ?)
            """,
            (provider, model_name, api_key_env, host),
        )
        conn.commit()


def get_model_config():
    """Return the single model_config row as a dict, or None if not set."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM model_config WHERE id = 1").fetchone()

    if not row:
        return {}
    model = dict(row)
    return model
