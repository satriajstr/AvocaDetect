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
        from backend.machine.model.test_svm import load_model

        model_path  = 'backend/machine/model/svm_model.pkl'
        scaler_path = 'backend/machine/model/scaler.pkl'

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            print("\n" + "=" * 60)
            print("  WARNING: Model belum di-training!")
            print("  Jalankan: python train_model.py")
            print("=" * 60)
            return False

        MODEL, SCALER = load_model(model_path, scaler_path)
        print("\n  [OK] Model SVM berhasil di-load!")
        return True

    except Exception as e:
        print(f"\n  [ERR] Error loading model: {e}")
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
        # 6. NORMALISASI ROI → GLCM (POIN 2: Gunakan levels=16 untuk visualisasi)
        # ------------------------------------------------------------------
        roi_normalized = normalize_for_glcm(roi_cropped, levels=16)
        
        # Ekstrak mask ROI untuk filtering background
        coords = cv2.findNonZero(binary_mask)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            roi_mask = binary_mask[y:y + h, x:x + w]
        else:
            roi_mask = None

        # ------------------------------------------------------------------
        # 7. EKSTRAKSI FITUR GLCM (dengan filtering background)
        # ------------------------------------------------------------------
        from backend.machine.feature_extraction.glcm import (
            compute_glcm_matrix,
            extract_features_from_glcm,
            get_feature_dict,
        )

        # Hitung GLCM dengan levels=32 untuk ekstraksi fitur (akurasi tinggi)
        roi_normalized_32 = normalize_for_glcm(roi_cropped, levels=32)
        glcm_features = compute_glcm_matrix(roi_normalized_32, mask=roi_mask)
        features = extract_features_from_glcm(glcm_features)
        features_dict = get_feature_dict(glcm_features)
        
        # Hitung GLCM dengan levels=16 untuk visualisasi (lebih jelas)
        glcm_visual = compute_glcm_matrix(roi_normalized, mask=roi_mask)

        # ------------------------------------------------------------------
        # 8. KLASIFIKASI SVM
        # ------------------------------------------------------------------
        features_scaled   = SCALER.transform(features)

        # Hitung probabilitas semua kelas via Platt scaling
        probabilities_raw = MODEL.predict_proba(features_scaled)[0]

        # Gunakan argmax dari predict_proba() sebagai prediksi final.
        # Alasan: MODEL.predict() menggunakan SVM decision boundary, sedangkan
        # predict_proba() menggunakan Platt scaling — keduanya bisa tidak sinkron.
        # argmax menjamin prediksi selalu = kelas dengan probabilitas TERTINGGI.
        import numpy as np
        prediction = int(np.argmax(probabilities_raw))
        category   = CATEGORIES[prediction]
        confidence = float(probabilities_raw[prediction] * 100)

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
            'prediction':    int(prediction),
            'category':      category,
            'confidence':    round(confidence, 2),
            'probabilities': {
                cat: round(float(probabilities_raw[i] * 100), 2)
                for i, cat in CATEGORIES.items()
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

        # [7] GLCM Heatmap (POIN 2: Visualisasi dengan colormap plasma)
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from io import BytesIO
        
        glcm_2d = glcm_visual[:, :, 0, 0]  # distance=1, angle=0°
        
        # Buat heatmap dengan matplotlib
        fig, ax = plt.subplots(figsize=(6, 6), dpi=85)
        im = ax.imshow(glcm_2d, cmap='plasma', interpolation='nearest', origin='lower')
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Probabilitas', rotation=270, labelpad=15, fontsize=9)
        
        # Grid
        levels_vis = glcm_2d.shape[0]
        ax.set_xticks(np.arange(0, levels_vis, max(1, levels_vis // 8)))
        ax.set_yticks(np.arange(0, levels_vis, max(1, levels_vis // 8)))
        ax.grid(True, color='white', linewidth=0.5, alpha=0.3)
        
        # Label
        ax.set_xlabel('Intensitas j', fontsize=10, fontweight='bold')
        ax.set_ylabel('Intensitas i', fontsize=10, fontweight='bold')
        ax.set_title('GLCM Matrix (16 levels)', fontsize=11, fontweight='bold')
        
        # Konversi ke BGR
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        buf.seek(0)
        img_arr = np.frombuffer(buf.read(), dtype=np.uint8)
        buf.close()
        plt.close(fig)
        
        glcm_colored = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        glcm_colored = cv2.resize(glcm_colored, (512, 512), interpolation=cv2.INTER_AREA)
        
        # Tambah thumbnail ROI
        roi_thumb = cv2.resize(roi_normalized, (80, 80), interpolation=cv2.INTER_NEAREST)
        roi_thumb_bgr = cv2.cvtColor(roi_thumb, cv2.COLOR_GRAY2BGR)
        glcm_colored[420:500, 420:500] = roi_thumb_bgr
        cv2.rectangle(glcm_colored, (419, 419), (501, 501), (255, 255, 255), 2)
        
        img7_glcm = img_to_base64(glcm_colored)

        # [8] Hasil SVM (POIN 3: Bounding box + label + overlay fitur GLCM)
        result_img = original_resized.copy()

        color_map_bgr = {
            'Mentah':          (70,  70, 255),
            'Setengah Matang': (50, 165, 255),
            'Matang':          (80, 200,  80),
            'Terlalu Matang':  (120, 60, 180),
        }
        border_color = color_map_bgr.get(category, (200, 200, 200))
        
        # Hitung bounding box dari mask
        if coords is not None:
            x_box, y_box, w_box, h_box = cv2.boundingRect(coords)
        else:
            x_box, y_box, w_box, h_box = 10, 10, 492, 492

        # Bounding box tebal
        cv2.rectangle(result_img, (x_box, y_box), (x_box+w_box, y_box+h_box), border_color, 4)
        
        # Corner markers
        corner_len, corner_thick = 25, 6
        cv2.line(result_img, (x_box, y_box), (x_box+corner_len, y_box), border_color, corner_thick)
        cv2.line(result_img, (x_box, y_box), (x_box, y_box+corner_len), border_color, corner_thick)
        cv2.line(result_img, (x_box+w_box, y_box), (x_box+w_box-corner_len, y_box), border_color, corner_thick)
        cv2.line(result_img, (x_box+w_box, y_box), (x_box+w_box, y_box+corner_len), border_color, corner_thick)
        cv2.line(result_img, (x_box, y_box+h_box), (x_box+corner_len, y_box+h_box), border_color, corner_thick)
        cv2.line(result_img, (x_box, y_box+h_box), (x_box, y_box+h_box-corner_len), border_color, corner_thick)
        cv2.line(result_img, (x_box+w_box, y_box+h_box), (x_box+w_box-corner_len, y_box+h_box), border_color, corner_thick)
        cv2.line(result_img, (x_box+w_box, y_box+h_box), (x_box+w_box, y_box+h_box-corner_len), border_color, corner_thick)

        # Label kategori + confidence
        label_text = f"{category} ({confidence:.1f}%)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), _ = cv2.getTextSize(label_text, font, 0.8, 2)
        
        label_x = x_box
        label_y = max(y_box - 10, text_h + 10)
        
        overlay = result_img.copy()
        cv2.rectangle(overlay, (label_x, label_y - text_h - 10), 
                      (label_x + text_w + 20, label_y + 5), border_color, -1)
        result_img = cv2.addWeighted(overlay, 0.7, result_img, 0.3, 0)
        cv2.putText(result_img, label_text, (label_x + 10, label_y - 5),
                    font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        # Overlay 4 fitur GLCM di pojok kiri bawah
        main_features = [
            ('Contrast', features_dict.get('Contrast (mean)', 0)),
            ('Correlation', features_dict.get('Correlation (mean)', 0)),
            ('Energy', features_dict.get('Energy (mean)', 0)),
            ('Homogeneity', features_dict.get('Homogeneity (mean)', 0)),
        ]
        
        feat_x, feat_y_start = 15, 512 - 140
        feat_box_w, feat_box_h = 230, 125
        
        overlay2 = result_img.copy()
        cv2.rectangle(overlay2, (feat_x - 5, feat_y_start - 5),
                      (feat_x + feat_box_w, feat_y_start + feat_box_h),
                      (30, 30, 30), -1)
        result_img = cv2.addWeighted(overlay2, 0.75, result_img, 0.25, 0)
        cv2.rectangle(result_img, (feat_x - 5, feat_y_start - 5),
                      (feat_x + feat_box_w, feat_y_start + feat_box_h),
                      (100, 100, 100), 1)
        
        cv2.putText(result_img, "GLCM Features:", (feat_x, feat_y_start + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        y_offset = feat_y_start + 40
        for feat_name, feat_value in main_features:
            text = f"{feat_name}: {feat_value:.4f}"
            cv2.putText(result_img, text, (feat_x, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
            y_offset += 22
        
        img8_svm = img_to_base64(result_img)

        # ------------------------------------------------------------------
        # 10. Cleanup & Response
        # ------------------------------------------------------------------
        os.remove(filepath)

        return jsonify({
            'success': True,
            'result':  result,
            'features': features_dict,
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
