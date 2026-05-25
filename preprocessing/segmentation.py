import cv2

def segment_image(image):
    """
    Segmentasi gambar menggunakan Otsu Thresholding.
    Otsu secara otomatis menentukan nilai threshold optimal
    berdasarkan distribusi histogram gambar.

    Return:
        mask   : gambar biner (objek=putih, background=hitam)
        result : gambar grayscale asli yang sudah di-mask
    """
    _, mask = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Terapkan mask ke gambar asli agar hanya area objek yang tersisa
    result = cv2.bitwise_and(image, image, mask=mask)
    return mask, result
