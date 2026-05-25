"""
Script untuk Training Model SVM - AvocaDetect
Dengan Background Removal dan Masking yang Proper

Jalankan file ini SEKALI SAJA untuk training model

Cara menjalankan:
    python train_model.py

Setelah training selesai, model akan tersimpan di:
    backend/machine/model/svm_model.pkl
    backend/machine/model/scaler.pkl
"""

import sys
import os

# Tambahkan path root ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.machine.model.train_svm import train_model

def main():
    """
    Fungsi utama untuk training model SVM dengan background removal
    """
    print("\n" + "=" * 70)
    print("AVOCADETECT - TRAINING MODEL SVM")
    print("dengan Background Removal & GLCM Masking")
    print("=" * 70)
    print("\nProses training akan dimulai...")
    print("Proses ini membutuhkan waktu lebih lama karena:")
    print("  1. Background removal untuk setiap gambar")
    print("  2. ROI extraction")
    print("  3. GLCM feature extraction")
    print("  4. SVM training")
    print("\nHarap tunggu...\n")
    
    # Path ke dataset
    dataset_path = 'dataset'
    
    # Cek apakah folder dataset ada
    if not os.path.exists(dataset_path):
        print(f"ERROR: Folder dataset tidak ditemukan di: {dataset_path}")
        print("Pastikan folder dataset berisi subfolder:")
        print("  - mentah/")
        print("  - setengah_matang/")
        print("  - matang/")
        print("  - terlalu_matang/")
        return
    
    # Training model
    try:
        model, scaler, accuracy = train_model(dataset_path)
        
        print("\n" + "=" * 70)
        print("TRAINING BERHASIL!")
        print("=" * 70)
        print(f"\nAkurasi Model: {accuracy*100:.2f}%")
        print("\nModel telah disimpan dan siap digunakan.")
        print("\nFitur yang diekstraksi:")
        print("  - Contrast (mean & std)")
        print("  - Dissimilarity (mean & std)")
        print("  - Homogeneity (mean & std)")
        print("  - Energy (mean & std)")
        print("  - Correlation (mean & std)")
        print("  - ASM (mean & std)")
        print("  Total: 12 fitur GLCM")
        print("\nAnda sekarang dapat menjalankan aplikasi web dengan:")
        print("    python run.py")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("TRAINING GAGAL!")
        print("=" * 70)
        print(f"\nError: {str(e)}")
        print("\nPastikan:")
        print("1. Folder dataset berisi gambar alpukat dengan background")
        print("2. Semua dependency sudah terinstall:")
        print("   pip install -r requirements.txt")
        print("3. Format gambar valid (jpg, jpeg, png)")
        print("4. Gambar memiliki kontras yang cukup untuk segmentasi")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
