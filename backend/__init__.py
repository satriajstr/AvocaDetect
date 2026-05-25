from flask import Flask
import os

def create_app():
    # Tentukan path root folder (folder tubes)
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Buat Flask app dengan path template dan static yang benar
    app = Flask(__name__,
                template_folder=os.path.join(root_path, 'frontend', 'ui'),
                static_folder=os.path.join(root_path, 'frontend'))
    
    # Register blueprint
    from backend.routes import bp
    app.register_blueprint(bp)
    
    return app
