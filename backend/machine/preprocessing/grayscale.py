import numpy as np

def to_grayscale(image):
    """
    Konversi gambar BGR (hasil cv2.imread) ke grayscale secara manual.
    Menggunakan rumus luminansi standar (ITU-R 601-2 Luma):
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    """
    if len(image.shape) == 2:
        return image
        
    if len(image.shape) == 3 and image.shape[2] == 3:
        b = image[:, :, 0].astype(np.float32)
        g = image[:, :, 1].astype(np.float32)
        r = image[:, :, 2].astype(np.float32)
        
        # Hitung luminansi
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        return np.clip(gray, 0, 255).astype(np.uint8)
        
    return image

