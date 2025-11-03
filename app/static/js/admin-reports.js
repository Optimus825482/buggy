// Admin Reports JavaScript
function generateReport() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        alert('Lütfen tarih aralığı seçin');
        return;
    }
    
    alert('Rapor oluşturma özelliği yakında eklenecek');
}
