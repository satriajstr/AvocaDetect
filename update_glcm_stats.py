"""
update_glcm_stats.py
====================
Script untuk menghitung rata-rata parameter GLCM per kelas klasifikasi
dari dataset, lalu menyimpannya ke eval_report.json.

Jalankan dengan:
    python update_glcm_stats.py

Script ini TIDAK melakukan retraining — hanya mengupdate bagian
glcm_class_stats di eval_report.json yang sudah ada.
"""

import os
import sys
import json
import numpy as np

# Pastikan root project ada di path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from backend.machine.feature_extraction.glcm import extract_all_features

CATEGORIES = ['Mentah', 'Setengah Matang', 'Matang', 'Terlalu Matang']
FEATURE_NAMES = [
    'Contrast (mean)', 'Correlation (mean)', 'Energy (mean)',
    'Homogeneity (mean)', 'ASM (mean)', 'Dissimilarity (mean)',
    'Contrast (std)', 'Correlation (std)', 'Energy (std)',
    'Homogeneity (std)', 'ASM (std)', 'Dissimilarity (std)',
]

DATASET_PATH   = 'dataset'
REPORT_PATH    = 'backend/machine/model/eval_report.json'

print("\n" + "=" * 60)
print("  UPDATE GLCM CLASS STATS — AvocaDetect")
print("=" * 60)

# ── 1. Ekstraksi fitur dari seluruh dataset ──────────────────────
print("\n[1/3] Ekstraksi fitur GLCM dari dataset...")
X, y = extract_all_features(DATASET_PATH)
print(f"  [OK] Total sampel  : {len(X)}")
print(f"  [OK] Jumlah fitur  : {X.shape[1]}")

# ── 2. Hitung rata-rata & std per kelas ─────────────────────────
print("\n[2/3] Menghitung statistik GLCM per kelas...")
glcm_class_stats = {}
for i, cat in enumerate(CATEGORIES):
    mask = y == i
    class_feats = X[mask]
    glcm_class_stats[cat] = {
        name: round(float(class_feats[:, j].mean()), 6)
        for j, name in enumerate(FEATURE_NAMES)
    }
    print(f"  [OK] {cat:<18} : {int(mask.sum())} sampel")

# ── 3. Update eval_report.json ───────────────────────────────────
print(f"\n[3/3] Update {REPORT_PATH}...")
if os.path.exists(REPORT_PATH):
    with open(REPORT_PATH, 'r') as f:
        report = json.load(f)
else:
    report = {}

report['glcm_class_stats'] = glcm_class_stats

with open(REPORT_PATH, 'w') as f:
    json.dump(report, f, indent=2)

print(f"  [OK] glcm_class_stats berhasil disimpan!")

print("\n" + "=" * 60)
print("  SELESAI! Restart server Flask lalu coba deteksi ulang.")
print("=" * 60 + "\n")
