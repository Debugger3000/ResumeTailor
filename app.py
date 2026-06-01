from dotenv import load_dotenv

load_dotenv()  # load environment vars first

from quart import Quart, render_template, request, jsonify, send_file
from blueprints.tailor import tailor_bp
from blueprints.apply import apply_bp
from blueprints.data import data_bp
from services.ai_model_control.run_local_model import start_ollama
from services.ai_model_control.run_cloud_model import start_cloud_model
from database.db import init_db
from services.ai_model_control.helpers import is_model_listed, is_model_local
from database.queries.ai_models import get_model_config
from services.ai_model_control.ollama_client import ollama_client
from services.ai_model_control.gemini_client import gemini_client 

# Run scripts
# ------
# Run Devleopment - Windows
# hypercorn app:app -c hypercorn.toml --reload
# Run - Linux with (.venv)
# ./.venv/bin/hypercorn app:app hypercorn.toml



# App instance var
app = Quart(__name__)

# Routes
app.register_blueprint(tailor_bp, url_prefix='/api')
app.register_blueprint(apply_bp, url_prefix='/api/apply')
app.register_blueprint(data_bp, url_prefix='/api/data')

# Base route
@app.route('/')
async def index():
    return await render_template('index.html')

@app.before_serving
async def _startup():
    init_db() # init db, if user has no database schema made, it will auto create tables and create file for them



    # does default model exist ?
        # if NOT, do not start any connection to cloud model or open local model
    if is_model_listed():
        model = get_model_config()
        # if no model config exists, it doesnt start any...
        if model:
            # returned something
            if is_model_local(model.get('provider')):
            # is local model
            # set up client variable for functions to use
                ollama_client.configure(model)
            # run local model and connect to it
                start_ollama(model)
            else:
                # connect to cloud model...
                # is cloud model
                gemini_client.configure(model)
                start_cloud_model(model)



    
    print("Starting server...")





if __name__ == '__main__':
    # Run with: hypercorn app:app --reload --bind 127.0.0.1:8000
    pass