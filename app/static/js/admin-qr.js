// Admin QR Codes JavaScript
async function loadQRCodes() {
    try {
        const response = await fetch('/api/locations');
        const data = await response.json();
        
        const qrList = document.getElementById('qrList');
        if (data.locations && data.locations.length > 0) {
            qrList.innerHTML = data.locations.map(loc => `
                <div class="qr-card">
                    <img src="${loc.qr_code_url}" alt="${loc.name}">
                    <h3>${loc.name}</h3>
                    <p>${loc.description || ''}</p>
                </div>
            `).join('');
        } else {
            qrList.innerHTML = '<p>Henüz QR kod yok</p>';
        }
    } catch (error) {
        console.error('Failed to load QR codes:', error);
    }
}

loadQRCodes();
