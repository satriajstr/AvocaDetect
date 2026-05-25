// ===== Smooth Scrolling =====
function scrollToDetection() {
    const detectionSection = document.getElementById('detection');
    detectionSection.scrollIntoView({ behavior: 'smooth' });
}

// Smooth scroll untuk semua link navigasi
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// ===== Handler untuk Upload Gambar =====
function handleUpload() {
    // Buat input file secara dinamis
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validasi tipe file
            if (!file.type.startsWith('image/')) {
                alert('Mohon pilih file gambar yang valid!');
                return;
            }
            
            // Preview gambar
            const reader = new FileReader();
            reader.onload = function(event) {
                displayImagePreview(event.target.result);
                showNotification('Gambar berhasil diupload! Klik tombol "Deteksi Kematangan" untuk memulai.', 'success');
            };
            reader.readAsDataURL(file);
        }
    };
    
    input.click();
}

// ===== Handler untuk Kamera =====
function handleCamera() {
    // Cek apakah browser mendukung getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Browser Anda tidak mendukung akses kamera!');
        return;
    }
    
    // Request akses kamera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            // Buat elemen video untuk preview
            const previewContainer = document.querySelector('.preview-placeholder');
            previewContainer.innerHTML = `
                <video id="cameraStream" autoplay playsinline style="width: 100%; max-width: 500px; border-radius: 12px;"></video>
                <div style="margin-top: 1rem;">
                    <button class="btn-primary" onclick="capturePhoto()" style="margin-right: 10px;">📸 Ambil Foto</button>
                    <button class="btn-secondary" onclick="stopCamera()">❌ Tutup Kamera</button>
                </div>
            `;
            
            const video = document.getElementById('cameraStream');
            video.srcObject = stream;
            
            // Simpan stream untuk digunakan nanti
            window.currentStream = stream;
            
            showNotification('Kamera berhasil diaktifkan!', 'success');
        })
        .catch(function(error) {
            console.error('Error accessing camera:', error);
            alert('Gagal mengakses kamera. Pastikan Anda memberikan izin akses kamera.');
        });
}

// ===== Fungsi untuk Capture Foto dari Kamera =====
function capturePhoto() {
    const video = document.getElementById('cameraStream');
    if (!video) return;
    
    // Buat canvas untuk capture
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Konversi ke data URL
    const imageDataUrl = canvas.toDataURL('image/jpeg');
    
    // Stop kamera
    stopCamera();
    
    // Tampilkan hasil capture
    displayImagePreview(imageDataUrl);
    showNotification('Foto berhasil diambil! Klik tombol "Deteksi Kematangan" untuk memulai.', 'success');
}

// ===== Fungsi untuk Stop Kamera =====
function stopCamera() {
    if (window.currentStream) {
        window.currentStream.getTracks().forEach(track => track.stop());
        window.currentStream = null;
    }
    
    // Reset preview
    resetPreview();
}

// ===== Fungsi untuk Display Image Preview =====
function displayImagePreview(imageUrl) {
    const previewContainer = document.querySelector('.preview-placeholder');
    previewContainer.innerHTML = `
        <img src="${imageUrl}" alt="Preview" style="max-width: 100%; max-height: 400px; border-radius: 12px; object-fit: contain;">
        <div style="margin-top: 1rem;">
            <button class="btn-secondary" onclick="resetPreview()">🔄 Ganti Gambar</button>
        </div>
    `;
    
    // Simpan image URL untuk deteksi
    window.currentImage = imageUrl;
}

// ===== Fungsi untuk Reset Preview =====
function resetPreview() {
    const previewContainer = document.querySelector('.preview-placeholder');
    previewContainer.innerHTML = `
        <span class="preview-icon">📷</span>
        <p>Area Preview Kamera</p>
        <p class="preview-hint">Upload gambar atau aktifkan kamera</p>
    `;
    
    window.currentImage = null;
}

// ===== Handler untuk Deteksi =====
function handleDetect() {
    // Cek apakah ada gambar yang diupload
    if (!window.currentImage) {
        showNotification('Mohon upload gambar atau ambil foto terlebih dahulu!', 'error');
        return;
    }
    
    // Tampilkan loading
    const resultContent = document.querySelector('.result-content');
    resultContent.innerHTML = `
        <div style="text-align: center;">
            <div class="loading-spinner"></div>
            <p style="margin-top: 1rem; color: var(--primary-green); font-weight: 600;">Sedang menganalisis gambar...</p>
        </div>
    `;
    
    // Simulasi proses deteksi (nanti akan diganti dengan API call ke backend)
    setTimeout(() => {
        // Hasil dummy untuk testing UI
        const dummyResults = [
            { label: 'Mentah', confidence: 15, color: '#FF6B6B' },
            { label: 'Matang Sempurna', confidence: 78, color: '#51CF66' },
            { label: 'Terlalu Matang', confidence: 7, color: '#FFA94D' }
        ];
        
        displayResults(dummyResults);
        showNotification('Deteksi selesai!', 'success');
    }, 2000);
}

// ===== Fungsi untuk Display Hasil Deteksi =====
function displayResults(results) {
    const resultContent = document.querySelector('.result-content');
    
    // Urutkan berdasarkan confidence tertinggi
    results.sort((a, b) => b.confidence - a.confidence);
    
    let html = '<div style="width: 100%;">';
    
    results.forEach(result => {
        html += `
            <div style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; color: var(--dark-green);">${result.label}</span>
                    <span style="font-weight: 700; color: ${result.color};">${result.confidence}%</span>
                </div>
                <div style="background: var(--gray-light); height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${result.color}; height: 100%; width: ${result.confidence}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    });
    
    // Tambahkan kesimpulan
    const topResult = results[0];
    html += `
        <div style="margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, var(--cream), var(--gray-light)); border-radius: 8px; border-left: 4px solid ${topResult.color};">
            <h4 style="color: var(--dark-green); margin-bottom: 0.5rem;">Kesimpulan:</h4>
            <p style="font-size: 1.1rem; font-weight: 600; color: ${topResult.color};">
                Alpukat terdeteksi dalam kondisi <strong>${topResult.label}</strong> dengan tingkat kepercayaan ${topResult.confidence}%
            </p>
        </div>
    `;
    
    html += '</div>';
    
    resultContent.innerHTML = html;
}

// ===== Fungsi untuk Notifikasi =====
function showNotification(message, type = 'info') {
    // Hapus notifikasi sebelumnya jika ada
    const existingNotif = document.querySelector('.notification');
    if (existingNotif) {
        existingNotif.remove();
    }
    
    // Buat elemen notifikasi
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    
    // Styling berdasarkan tipe
    const colors = {
        success: '#51CF66',
        error: '#FF6B6B',
        info: '#4DABF7'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    // Hapus setelah 3 detik
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== CSS untuk Loading Spinner =====
const style = document.createElement('style');
style.textContent = `
    .loading-spinner {
        border: 4px solid var(--gray-light);
        border-top: 4px solid var(--primary-green);
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===== Navbar Scroll Effect =====
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
    } else {
        navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }
});

// ===== Console Welcome Message =====
console.log('%c🥑 AvocaDetect ', 'background: #6B8E23; color: white; font-size: 20px; padding: 10px; border-radius: 5px;');
console.log('%cKlasifikasi Kematangan Alpukat Berbasis Tekstur', 'color: #6B8E23; font-size: 14px;');
console.log('%cTugas Besar Pengolahan Citra Digital', 'color: #999; font-size: 12px;');
