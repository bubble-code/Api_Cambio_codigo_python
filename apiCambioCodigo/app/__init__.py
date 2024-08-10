from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes import main_bp
    from app.Routers.orden_routes import orden_bp
    app.register_blueprint(orden_bp)
    app.register_blueprint(main_bp)
    
    return app
