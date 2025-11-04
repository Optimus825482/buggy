/**
 * Shuttle Call - Notification Sound Generator
 * Basit bildirim sesi oluşturur (ses dosyası olmadan)
 */

// Web Audio API ile bildirim sesi oluştur
function generateNotificationSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Oscillator (ses dalgası) oluştur
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        // Bağlantıları kur
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Ses ayarları - Hoş bir bildirim sesi
        oscillator.type = 'sine'; // Yumuşak ses
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800 Hz
        oscillator.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + 0.1); // 1200 Hz'e yüksel
        
        // Ses seviyesi - Fade out
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        // Sesi çal
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
        
        console.log('[Sound] Notification sound generated and played');
        return true;
    } catch (error) {
        console.error('[Sound] Error generating notification sound:', error);
        return false;
    }
}

// Çift beep sesi (daha dikkat çekici)
function generateDoubleBeep() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // İlk beep
        const osc1 = audioContext.createOscillator();
        const gain1 = audioContext.createGain();
        osc1.connect(gain1);
        gain1.connect(audioContext.destination);
        osc1.frequency.value = 880; // A5 notası
        osc1.type = 'sine';
        gain1.gain.setValueAtTime(0.3, audioContext.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        osc1.start(audioContext.currentTime);
        osc1.stop(audioContext.currentTime + 0.15);
        
        // İkinci beep (biraz daha yüksek)
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.frequency.value = 1046.5; // C6 notası
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime + 0.2);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
        osc2.start(audioContext.currentTime + 0.2);
        osc2.stop(audioContext.currentTime + 0.4);
        
        console.log('[Sound] Double beep notification played');
        return true;
    } catch (error) {
        console.error('[Sound] Error generating double beep:', error);
        return false;
    }
}

// Üçlü chime sesi (en hoş)
function generateChimeSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const frequencies = [523.25, 659.25, 783.99]; // C, E, G (majör akor)
        
        frequencies.forEach((freq, index) => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = freq;
            oscillator.type = 'sine';
            
            const startTime = audioContext.currentTime + (index * 0.1);
            gainNode.gain.setValueAtTime(0.2, startTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.5);
            
            oscillator.start(startTime);
            oscillator.stop(startTime + 0.5);
        });
        
        console.log('[Sound] Chime notification played');
        return true;
    } catch (error) {
        console.error('[Sound] Error generating chime sound:', error);
        return false;
    }
}

// Export fonksiyonlar
window.NotificationSound = {
    generate: generateNotificationSound,
    doubleBeep: generateDoubleBeep,
    chime: generateChimeSound
};

console.log('[Sound] Notification sound generator loaded');
