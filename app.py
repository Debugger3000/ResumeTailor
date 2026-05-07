from dotenv import load_dotenv

load_dotenv()  # load environment vars first

from quart import Quart, render_template, request, jsonify, send_file
from blueprints.tailor import tailor_bp
from blueprints.apply import apply_bp
from services.ollama_lifecycle import start_ollama

# Run Devleopment
# hypercorn app:app -c hypercorn.toml --reload

# App instance var
app = Quart(__name__)

# Routes
app.register_blueprint(tailor_bp, url_prefix='/api')
app.register_blueprint(apply_bp, url_prefix='/api/apply')

# Base route
@app.route('/')
async def index():
    return await render_template('index.html')

@app.before_serving
async def _startup():
    #start_ollama()
    print("Starting server...")





if __name__ == '__main__':
    # Run with: hypercorn app:app --reload --bind 127.0.0.1:8000
    pass