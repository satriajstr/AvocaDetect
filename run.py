"""
Entry Point Aplikasi AvocaDetect
Jalankan file ini untuk menjalankan aplikasi web Flask

Cara menjalankan:
    python run.py

Aplikasi akan berjalan di:
    http://localhost:5000
"""

import os
from backend.web import create_app

# Buat aplikasi Flask
app = create_app()

if __name__ == '__main__':
    # Ambil PORT dari environment variable (untuk Railway)
    port = int(os.environ.get('PORT', 5000))
    
    # Jalankan aplikasi
    # debug=False untuk production
    # host='0.0.0.0' agar bisa diakses dari luar
    app.run(debug=False, host='0.0.0.0', port=port)
