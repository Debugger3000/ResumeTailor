import os, time, tempfile
from pathlib import Path
from quart import Blueprint, request, jsonify, send_file
from database.db import get_conn
from database.queries.get_skill_catalog import get_skills_catalog
from database.queries.post_user_skills import add_user_skills
from database.queries.user_profile import get_user_profile, update_user_profile
from database.queries.ai_models import save_model_config, get_model_config
from services.apply.apply_agent import get_full_user_data
from database.queries.experience import get_user_experience, create_user_experience, patch_user_experience, delete_user_experience
from database.queries.education import get_user_education, create_user_education, patch_user_education, delete_user_education
from services.ai_model_control.helpers import ollama_status, is_model_local
from services.ai_model_control.run_local_model import stop_ollama, start_ollama
from services.ai_model_control.run_cloud_model import start_cloud_model
from services.ai_model_control.ollama_client import ollama_client
from services.ai_model_control.gemini_client import gemini_client


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


@data_bp.route('/education', methods=['GET'])
async def get_education():
    return jsonify(get_user_education())


@data_bp.route('/education', methods=['POST'])
async def create_education():
    body = await request.get_json() or {}
    new_id = create_user_education(body)
    return jsonify({"ok": True, "id": new_id}), 201


@data_bp.route('/education/<int:edu_id>', methods=['PATCH'])
async def patch_education(edu_id):
    body = await request.get_json() or {}
    updated = patch_user_education(edu_id, body)
    if not updated:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "id": edu_id})


@data_bp.route('/education/<int:edu_id>', methods=['DELETE'])
async def delete_education(edu_id):
    deleted = delete_user_education(edu_id)
    if not deleted:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "id": edu_id})




@data_bp.route('/model', methods=['POST'])
async def save_model():
    body = await request.get_json() or {}

    print(body)

    provider    = (body.get('provider') or '').strip().lower()
    provider_category = (body.get('provider_category') or '').strip().lower()
    model_name  = (body.get('model_name') or '').strip()
    host        = (body.get('host') or '').strip() or None
    api_key_env = (body.get('api_key_env') or None)

    print(provider_category)

    print("api key for cloud modellll")
    print(api_key_env)

    # make sure provider names are correct...
    if provider not in ('ollama', 'anthropic', 'openai', 'google'):
        return {"ok": False, "error": "Invalid provider"}, 400
    if not model_name:
        return {"ok": False, "error": "model_name is required"}, 400
    
    # save model config to db
    save_model_config(
        provider=provider,
        provider_category=provider_category,
        model_name=model_name,
        host=host,
        api_key_env=api_key_env,
    )

    return {"ok": True}

# route called, after server updates model config, to update ollama_client object and restart ollama with new model config
@data_bp.route('/model/updated', methods=['POST'])
async def updated_model_run():
    body = await request.get_json() or {}
    kind = (body.get('provider_category') or 'cloud').strip().lower() 
    want_local = (kind == 'local')

    models = get_model_config()   # list of 0–2 rows
    print(models)

    # Find the saved config for the requested side
    model = next(
        (m for m in models if is_model_local(m.get('provider')) == want_local),
        None,
    )

    # Not in the database → do nothing
    if not model:
        return {"ok": False, "error": f"No {kind} model configured"}, 400

    try:
        if is_model_local(model.get('provider')):
            stop_ollama()
            time.sleep(0.5)            # let the port release
            ollama_client.configure(model)
            start_ollama(model)
        else:
            # cloud — just (re)configure the client, nothing to spin up
            gemini_client.configure(model)
            # start_cloud_model(model)

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500



@data_bp.route('/model', methods=['GET'])
async def get_model():
    model = get_model_config()
    print(model)
    return jsonify(model)


# -----
# Get current model / model connection status
@data_bp.route('/model/status', methods=['GET'])
async def get_model_status():
    models = get_model_config()

    if models == None:
        return jsonify({
            "running": False,
            "provider": None,
            "configured": False,
            "model_name": None,
            "host": None,
            "loaded_models": [],
            "error": "No model configured",
        })


    kind = request.args.get('type', 'cloud')
    want_local = (kind == 'local')

    model = next(
        (m for m in models if is_model_local(m.get('provider')) == want_local),
        None,
    )

    # no config exists currently...
    if not model:
        return jsonify({
            "running": False,
            "provider": None,
            "configured": False,
            "model_name": None,
            "host": None,
            "loaded_models": [],
            "error": "No model configured",
        })

    if is_model_local(model.get('provider')):
            return jsonify(ollama_status(model))

    # else:
        # return cloud_status()

    # TODO: cloud_status
    return jsonify({
        "running": True,  # assume cloud is reachable until we add a real check
        "provider": model.get('provider'),
        "configured": True,
        "model_name": model.get('model_name'),
        "host": model.get('host'),
        "loaded_models": [],
        "error": None,
    })
    


# test model get
@data_bp.route('/model/test-full-profile', methods=['GET'])
async def get_profile_full():
    return get_full_user_data()


