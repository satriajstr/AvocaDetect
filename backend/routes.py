from flask import render_template, Blueprint

# Buat blueprint untuk routes
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Route untuk halaman utama"""
    return render_template('index.html')

# Route untuk deteksi akan ditambahkan nanti
# @bp.route('/detect', methods=['POST'])
# def detect():
#     pass
