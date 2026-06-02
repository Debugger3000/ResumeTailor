
from database.db import get_conn
from typing import TypedDict, Optional
from datetime import datetime

def save_model_config(provider, provider_category, model_name, host=None, api_key_env=None):
    """Replace the single model_config row with the given values."""
    with get_conn() as conn:        # adjust to whatever your connection helper is
        # delete row from either local or cloud config...
        conn.execute("DELETE FROM model_config WHERE provider_category = ?", (provider_category,),)
        conn.execute(
            """
            INSERT INTO model_config (provider, provider_category, model_name, api_key_env, host)
            VALUES (?, ?, ?, ?, ?)
            """,
            (provider, provider_category, model_name, api_key_env, host),
        )
        conn.commit()




class ModelConfig(TypedDict):
    id: int
    provider: str
    provider_category: str
    model_name: str
    api_key_env: Optional[str]
    host: Optional[str]
    temperature: float
    updated_at: datetime

def get_model_config() -> Optional[ModelConfig]:
    """Return the single model_config row as a dict, or None if not set."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM model_config").fetchall()

    if not rows:
        return None
    return [dict(row) for row in rows]
