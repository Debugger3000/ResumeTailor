import sqlite3
from pathlib import Path
from contextlib import contextmanager
from database.queries.populate_skill_catalog import seed_skill_catalog

DB_PATH = Path(__file__).parent / "data" / "autojobdata.db"


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript("""

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                proficiency TEXT,
                years_experience REAL
            );
                           
            CREATE TABLE IF NOT EXISTS skill_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT,
                is_seed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS model_config (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL DEFAULT 'ollama',
                provider_category TEXT NOT NULL DEFAULT 'cloud',
                model_name TEXT NOT NULL DEFAULT 'llama3',
                api_key_env TEXT,
                host TEXT,
                temperature REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
                           
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                -- personal
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                full_name TEXT,
                preferred_name TEXT,
                pronouns TEXT,
                email TEXT,
                phone TEXT,
                date_of_birth TEXT,
                account_password TEXT,
                -- address
                street TEXT,
                city TEXT,
                state_province TEXT,
                postal_code TEXT,
                country TEXT,
                -- links
                linkedin TEXT,
                github TEXT,
                portfolio TEXT,
                -- work auth
                work_auth_country TEXT,
                work_auth_status TEXT,
                requires_sponsorship_now INTEGER,
                requires_sponsorship_future INTEGER,
                criminal_history TEXT,
                -- preferences
                desired_salary TEXT,
                desired_salary_currency TEXT,
                willing_to_relocate INTEGER,
                open_to_travel INTEGER,
                -- demographics
                gender TEXT,
                hispanic_latino TEXT,
                race_ethnicity TEXT,
                visible_minority TEXT,
                indigenous_status TEXT,
                veteran_status TEXT,
                disability_status TEXT,
                sexual_orientation TEXT,
                transgender TEXT,
                -- compliance
                is_18_or_older INTEGER,
                can_provide_work_documents INTEGER,
                non_compete_active INTEGER,
                previously_employed_here INTEGER,
                current_country TEXT,
                eligible_for_work_current_country INTEGER,
                allow_data_use INTEGER,
                --Language
                language    TEXT NOT NULL,
                is_native   INTEGER,
                overall     TEXT,
                reading     TEXT,
                speaking    TEXT,
                writing     TEXT,              
                
                -- open questions
                why_this_company TEXT,
                why_this_role TEXT,
                greatest_strength TEXT,
                biggest_weakness TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS work_experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                title TEXT,
                location TEXT,
                start_date TEXT,
                end_date TEXT,
                is_current INTEGER DEFAULT 0,
                summary TEXT,
                tech_stack TEXT,  -- JSON array stored as text
                sort_order INTEGER DEFAULT 0
            );
                           
            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school TEXT,
                program TEXT,
                degree_type TEXT,
                gpa TEXT,
                start_date TEXT,
                end_date TEXT,
                currently_enrolled INTEGER,
                summary TEXT,
                sort_order INTEGER DEFAULT 0
            );

        """)
        conn.commit()

        # db setup
        seed_skill_catalog(conn) # populate skill_catalog list 
    finally:
        conn.close()


# expose sqlite connection variable to server environment
@contextmanager
def get_conn():
    """Context manager for DB connections — auto-closes, returns dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()



# CREATE TABLE IF NOT EXISTS applications (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 url TEXT NOT NULL,
#                 company TEXT,
#                 role TEXT,
#                 applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 resume_path TEXT,
#                 job_description TEXT,
#                 status TEXT DEFAULT 'submitted',
#                 notes TEXT
# #             );
# CREATE INDEX IF NOT EXISTS idx_applications_url ON applications(url);
#             CREATE INDEX IF NOT EXISTS idx_applications_applied_at ON applications(applied_at);