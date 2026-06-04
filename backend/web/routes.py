"""
Flask Routes - AvocaDetect
============================
Endpoint API untuk klasifikasi kematangan alpukat.

Endpoints:
  GET  /              → Halaman utama
  GET  /model-info    → Informasi evaluasi model (akurasi, dll.)
  POST /detect        → Klasifikasi gambar alpukat

Response /detect:
  {
    "success": true,
    "result":  { prediction, category, confidence, probabilities },
    "features": { nama_fitur: nilai, ... },   ← tabel 12 fitur GLCM
    "images": {
      "original"  : "data:image/png;base64,...",
      "grayscale" : "...",
      "denoised"  : "...",
      "mask"      : "...",   ← binary mask (amber/hitam)
      "masked"    : "...",   ← masked original (objek berwarna, bg putih)
      "contour"   : "...",   ← original + kontur kuning
      "glcm"      : "...",   ← heatmap GLCM
      "svm"       : "..."    ← hasil klasifikasi SVM
    }
  }

Author: AvocaDetect Team
"""

import os
import json
import base64
import tempfile

import cv2
import numpy as np
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

# Global model state (lazy-load saat pertama kali dibutuhkan)
MODEL  = None
SCALER = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

CATEGORIES = {
    0: 'Mentah',
    1: 'Setengah Matang',
    2: 'Matang',
    3: 'Terlalu Matang',
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def img_to_base64(img_bgr):
    """Konversi gambar BGR numpy array ke data URI base64 PNG."""
    _, buffer = cv2.imencode('.png', img_bgr)
    encoded   = base64.b64encode(buffer).decode('utf-8')
    return f'data:image/png;base64,{encoded}'


def load_ml_model():
    """Lazy-load model SVM dan scaler dari file .pkl."""
    global MODEL, SCALER

    if MODEL is not None and SCALER is not None:
        return True

    try:
        import pickle

        model_path  = 'backend/machine/model/svm_model.pkl'
        scaler_path = 'backend/machine/model/scaler.pkl'

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            print("\n" + "=" * 60)
            print("  WARNING: Model belum di-training!")
            print("  Jalankan: python train_model.py")
            print("=" * 60)
            return False

        # Load model dengan pickle
        with open(model_path, 'rb') as f:
            MODEL = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            SCALER = pickle.load(f)
        
        print("\n  [OK] Model SVM berhasil di-load!")
        return True

    except Exception as e:
        print(f"\n  [ERR] Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# ROUTES
# =============================================================================

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/model-info')
def model_info():
    """
    Return informasi evaluasi model dari eval_report.json.
    Digunakan oleh frontend untuk menampilkan akurasi di landing page.
    """
    report_path = 'backend/machine/model/eval_report.json'

    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
        return jsonify({'success': True, 'report': report})

    return jsonify({
        'success': False,
        'error': 'Eval report belum ada. Jalankan python train_model.py terlebih dahulu.'
    })


@bp.route('/detect', methods=['POST'])
def detect():
    """
    Endpoint utama klasifikasi kematangan alpukat.

    Input : multipart/form-data dengan field 'image' (jpg/png)
    Output: JSON dengan hasil prediksi, 8 gambar visualisasi, tabel fitur GLCM
    """
    try:
        # ------------------------------------------------------------------
        # 1. Validasi Model
        # ------------------------------------------------------------------
        if MODEL is None or SCALER is None:
            if not load_ml_model():
                return jsonify({
                    'success': False,
                    'error': 'Model belum di-training. Jalankan: python train_model.py'
                }), 500

        # ------------------------------------------------------------------
        # 2. Validasi Input
        # ------------------------------------------------------------------
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Field gambar tidak ditemukan'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Tidak ada gambar yang dipilih'}), 400
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Format tidak didukung (gunakan jpg/jpeg/png)'}), 400

        # ------------------------------------------------------------------
        # 3. Simpan file sementara
        # ------------------------------------------------------------------
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)

        image = cv2.imread(filepath)
        if image is None:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Gagal membaca gambar'}), 400

        # ------------------------------------------------------------------
        # 4. PREPROCESSING PIPELINE
        # ------------------------------------------------------------------
        from backend.machine.preprocessing.preprocessing import (
            preprocess_image,
            normalize_for_glcm,
            get_masked_original,
            get_contour_overlay,
        )

        (original_resized, gray, denoised,
         binary_mask, gray_masked, roi_cropped) = preprocess_image(image)

        # Validasi: objek harus cukup besar (min 1000 piksel)
        non_zero = cv2.countNonZero(binary_mask)
        if non_zero < 1000:
            os.remove(filepath)
            return jsonify({
                'success': False,
                'error': (
                    'Gagal mengidentifikasi objek alpukat. '
                    'Pastikan gambar jelas dengan latar belakang kontras.'
                )
            }), 400

        # ------------------------------------------------------------------
        # 5. VISUALISASI SEGMENTASI
        # ------------------------------------------------------------------
        # Masked original: objek berwarna, background putih
        masked_original  = get_masked_original(original_resized, binary_mask)
        # Contour overlay: original + garis kuning di tepi objek
        contour_overlay  = get_contour_overlay(original_resized, binary_mask)

        # ------------------------------------------------------------------
        # 6. NORMALISASI ROI → GLCM
        # ------------------------------------------------------------------
        roi_normalized = normalize_for_glcm(roi_cropped, levels=32)

        # ------------------------------------------------------------------
        # 7. EKSTRAKSI FITUR GLCM
        # ------------------------------------------------------------------
        from backend.machine.feature_extraction.glcm import (
            compute_glcm_matrix,
            extract_features_from_glcm,
            get_feature_dict,
            create_glcm_visualization,
        )

        glcm          = compute_glcm_matrix(roi_normalized)
        features      = extract_features_from_glcm(glcm)
        features_dict = get_feature_dict(glcm)

        # ------------------------------------------------------------------
        # 8. KLASIFIKASI SVM
        # ------------------------------------------------------------------
        features_scaled   = SCALER.transform(features)

        # Hitung probabilitas semua kelas via Platt scaling
        # probabilities_raw[i] = P(kelas MODEL.classes_[i]) — urutan kelas
        # HARUS dibaca dari MODEL.classes_, bukan diasumsikan [0,1,2,3].
        probabilities_raw = MODEL.predict_proba(features_scaled)[0]
        class_order       = MODEL.classes_.tolist()   # urutan kelas sesuai model

        # ── Bangun dict { label_int: probabilitas } sesuai urutan model ──
        prob_by_label = {
            int(cls): float(prob)
            for cls, prob in zip(class_order, probabilities_raw)
        }

        # ── Prediksi = kelas dengan probabilitas TERTINGGI ──────────────
        # Menggunakan argmax atas dict prob_by_label sehingga selalu sinkron
        # antara kategori yang ditampilkan dan bar probabilitas di grafik.
        # (MODEL.predict() bisa berbeda karena menggunakan decision boundary
        # SVM yang berbeda dari Platt-scaled probability — ini diketahui dan
        # sengaja diabaikan agar tampilan konsisten.)
        import numpy as np
        prediction = int(max(prob_by_label, key=prob_by_label.get))
        category   = CATEGORIES[prediction]
        confidence = float(prob_by_label[prediction] * 100)

        # Tolak prediksi dengan confidence sangat rendah
        if confidence < 25:
            os.remove(filepath)
            return jsonify({
                'success': False,
                'error': (
                    'Confidence terlalu rendah. '
                    'Pastikan gambar menampilkan alpukat dengan jelas.'
                )
            }), 400

        result = {
            'prediction':    prediction,
            'category':      category,
            'confidence':    round(confidence, 2),
            # Kirim semua probabilitas, dipetakan dari label kelas yang benar
            'probabilities': {
                CATEGORIES[label]: round(prob * 100, 2)
                for label, prob in prob_by_label.items()
                if label in CATEGORIES          # abaikan label tak dikenal
            },
        }

        # ------------------------------------------------------------------
        # 9. BUAT GAMBAR VISUALISASI
        # ------------------------------------------------------------------

        # [1] Citra Asli
        img1_original = img_to_base64(original_resized)

        # [2] Grayscale
        img2_gray = img_to_base64(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))

        # [3] Noise Reduction
        img3_denoised = img_to_base64(cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR))

        # [4] Binary Mask — amber/hitam (lebih profesional dari hijau solid)
        mask_display = np.zeros((512, 512, 3), dtype=np.uint8)
        mask_display[binary_mask == 255] = [60, 180, 230]    # amber/gold = objek
        mask_display[binary_mask == 0]   = [25, 25, 25]       # hampir hitam = background
        img4_mask = img_to_base64(mask_display)

        # [5] Masked Original — objek berwarna, background putih
        img5_masked = img_to_base64(masked_original)

        # [6] Contour Overlay — original + outline kuning
        img6_contour = img_to_base64(contour_overlay)

        # [7] GLCM Heatmap - Gunakan fungsi visualisasi yang lebih baik
        glcm_visualization = create_glcm_visualization(glcm, roi_normalized, size=512)
        img7_glcm = img_to_base64(glcm_visualization)

        # [8] Hasil SVM — original + border warna + teks prediksi
        result_img = original_resized.copy()

        color_map_bgr = {
            'Mentah':          (70,  70, 255),   # merah
            'Setengah Matang': (50, 165, 255),   # orange
            'Matang':          (80, 200,  80),   # hijau
            'Terlalu Matang':  (120, 60, 180),   # ungu
        }
        border_color = color_map_bgr.get(category, (200, 200, 200))

        # Border tebal
        cv2.rectangle(result_img, (0, 0), (511, 511), border_color, 12)

        # Semi-transparent background untuk teks
        overlay = result_img.copy()
        cv2.rectangle(overlay, (8, 8), (503, 125), (15, 15, 15), -1)
        result_img = cv2.addWeighted(overlay, 0.65, result_img, 0.35, 0)

        # Teks prediksi
        cv2.putText(
            result_img, category, (25, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA
        )
        cv2.putText(
            result_img, f"Confidence: {confidence:.1f}%", (25, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (210, 210, 210), 2, cv2.LINE_AA
        )
        img8_svm = img_to_base64(result_img)

        # ------------------------------------------------------------------
        # 10. Cleanup & Response
        # ------------------------------------------------------------------
        os.remove(filepath)

        # ------------------------------------------------------------------
        # Load glcm_class_stats dari eval_report jika ada
        # ------------------------------------------------------------------
        glcm_class_stats = {}
        report_path = 'backend/machine/model/eval_report.json'
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                _report = json.load(f)
            glcm_class_stats = _report.get('glcm_class_stats', {})

        return jsonify({
            'success': True,
            'result':  result,
            'features': features_dict,
            'glcm_class_stats': glcm_class_stats,
            'images': {
                'original':     img1_original,
                'grayscale':    img2_gray,
                'denoised':     img3_denoised,
                'mask':         img4_mask,
                'segmentation': img4_mask,   # alias untuk kompatibilitas JS lama
                'masked':       img5_masked,
                'contour':      img6_contour,
                'glcm':         img7_glcm,
                'svm':          img8_svm,
            },
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Terjadi kesalahan internal: {str(e)}'}), 500
