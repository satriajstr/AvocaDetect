"""
Inisialisasi aplikasi Flask AvocaDetect
"""

from flask import Flask
import os

def create_app():
    """
    Factory function untuk membuat aplikasi Flask
    """
    # Tentukan path root folder (folder tubes)
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Buat Flask app dengan path template dan static yang benar
    app = Flask(__name__,
                template_folder=os.path.join(root_path, 'frontend', 'ui'),
                static_folder=os.path.join(root_path, 'frontend'))
    
    # Register blueprint
    from backend.web.routes import bp, load_ml_model
    app.register_blueprint(bp)
    
    # Auto-load model saat aplikasi start
    with app.app_context():
        print("\n" + "="*70)
        print("AVOCADETECT - Starting Application")
        print("="*70)
        load_ml_model()
        print("="*70 + "\n")
    
    return app
