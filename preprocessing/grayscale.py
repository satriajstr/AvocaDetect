import cv2

def to_grayscale(image):
    """
    Konversi gambar BGR (hasil cv2.imread) ke grayscale.
    Grayscale diperlukan untuk ekstraksi fitur GLCM.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
