import numpy as np

# Ukuran standar untuk semua gambar dalam pipeline
TARGET_SIZE = (512, 512)

def resize_image(image):
    """
    Resize gambar ke ukuran TARGET_SIZE (512x512) menggunakan algoritma
    Bilinear Interpolation manual berbasis NumPy (Tanpa OpenCV).
    Mendukung gambar berwarna (3D) dan grayscale (2D).
    """
    h_src, w_src = image.shape[:2]
    w_dst, h_dst = TARGET_SIZE
    
    if h_src == h_dst and w_src == w_dst:
        return image

    # Buat koordinat grid pixel target
    y_dst, x_dst = np.meshgrid(np.arange(h_dst), np.arange(w_dst), indexing='ij')

    # Petakan koordinat target ke koordinat sumber secara linear
    y_src = y_dst * (h_src - 1) / (h_dst - 1)
    x_src = x_dst * (w_src - 1) / (w_dst - 1)

    # Tentukan 4 piksel tetangga terdekat
    y0 = np.floor(y_src).astype(np.int32)
    y1 = np.ceil(y_src).astype(np.int32)
    x0 = np.floor(x_src).astype(np.int32)
    x1 = np.ceil(x_src).astype(np.int32)

    # Pastikan koordinat tidak keluar dari batas gambar asli
    y0 = np.clip(y0, 0, h_src - 1)
    y1 = np.clip(y1, 0, h_src - 1)
    x0 = np.clip(x0, 0, w_src - 1)
    x1 = np.clip(x1, 0, w_src - 1)

    # Hitung bobot selisih interpolasi
    dy = y_src - y0
    dx = x_src - x0

    # Lakukan interpolasi secara vectorized
    if len(image.shape) == 3:
        dy = dy[:, :, None]
        dx = dx[:, :, None]
        
        i00 = image[y0, x0].astype(np.float32)
        i01 = image[y0, x1].astype(np.float32)
        i10 = image[y1, x0].astype(np.float32)
        i11 = image[y1, x1].astype(np.float32)
    else:
        i00 = image[y0, x0].astype(np.float32)
        i01 = image[y0, x1].astype(np.float32)
        i10 = image[y1, x0].astype(np.float32)
        i11 = image[y1, x1].astype(np.float32)

    # Formula interpolasi bilinear
    resized = (
        i00 * (1 - dy) * (1 - dx) +
        i01 * (1 - dy) * dx +
        i10 * dy * (1 - dx) +
        i11 * dy * dx
    )

    return np.clip(resized, 0, 255).astype(np.uint8)

