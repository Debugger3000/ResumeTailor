import os
import tempfile
from pathlib import Path
from quart import Blueprint, request, jsonify, send_file
from database.db import get_conn
from database.queries.get_skill_catalog import get_skills_catalog
from database.queries.post_user_skills import add_user_skills
from database.queries.user_profile import get_user_profile, update_user_profile


# blueprint - route name is 'tailor'
data_bp = Blueprint('data', __name__)


# Main Endpoint for Tailor process 
# ---
@data_bp.route('/skills', methods=['GET'])
async def get_skills():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM skills ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@data_bp.route('/skills', methods=['POST'])
async def save_skills():
    body = await request.get_json()
    incoming = body.get('skills', [])
    count = add_user_skills(incoming)
    return {"ok": True, "count": count}


@data_bp.route("/skills/catalog", methods=["GET"])
async def skills_catalog():
    skills_catalog = get_skills_catalog()
    # print(skills_catalog)
    return skills_catalog


# user profile data
@data_bp.route('/profile', methods=['GET'])
async def get_profile():
    return get_user_profile()


@data_bp.route('/profile', methods=['PATCH'])
async def patch_profile():
    body = await request.get_json()
    update_user_profile(body)
    return {"ok": True}