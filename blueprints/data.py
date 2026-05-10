import os
import tempfile
from pathlib import Path
from quart import Blueprint, request, jsonify, send_file
from database.db import get_conn
from database.queries.get_skill_catalog import get_skills_catalog
from database.queries.post_user_skills import add_user_skills
from database.queries.user_profile import get_user_profile, update_user_profile
from database.queries.ai_models import save_model_config, get_model_config
from services.apply_agent import get_full_user_data
from database.queries.experience import get_user_experience, create_user_experience, patch_user_experience, delete_user_experience

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


# GET /api/data/experience → array of rows
# POST /api/data/experience → create (returns {id: ...})
# PATCH /api/data/experience/<id> → update
# DELETE /api/data/experience/<id> → delete


@data_bp.route('/experience', methods=['GET'])
async def get_experience():
    return jsonify(get_user_experience())


@data_bp.route('/experience', methods=['POST'])
async def create_experience():
    body = await request.get_json() or {}
    new_id = create_user_experience(body)
    return jsonify({"ok": True, "id": new_id}), 201


@data_bp.route('/experience/<int:exp_id>', methods=['PATCH'])
async def patch_experience(exp_id):
    body = await request.get_json() or {}
    updated = patch_user_experience(exp_id, body)
    if not updated:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "id": exp_id})


@data_bp.route('/experience/<int:exp_id>', methods=['DELETE'])
async def delete_experience(exp_id):
    deleted = delete_user_experience(exp_id)
    if not deleted:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "id": exp_id})




@data_bp.route('/model', methods=['POST'])
async def save_model():
    body = await request.get_json() or {}

    print(body)

    provider    = (body.get('provider') or '').strip().lower()
    model_name  = (body.get('model_name') or '').strip()
    host        = (body.get('host') or '').strip() or None
    api_key_env = (body.get('api_key_env') or None)

    # make sure provider names are correct...
    if provider not in ('ollama', 'anthropic', 'openai', 'google'):
        return {"ok": False, "error": "Invalid provider"}, 400
    if not model_name:
        return {"ok": False, "error": "model_name is required"}, 400
    
    # save model config to db
    save_model_config(
        provider=provider,
        model_name=model_name,
        host=host,
        api_key_env=api_key_env,
    )

    return {"ok": True}

@data_bp.route('/model', methods=['GET'])
async def get_model():
    model = get_model_config()
    print(model)
    return model



# test model get
@data_bp.route('/model/test-full-profile', methods=['GET'])
async def get_profile_full():
    return get_full_user_data()


