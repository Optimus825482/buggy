"""
Buggy Call - System Reset Route
Emergency system reset functionality
"""
from flask import Blueprint, jsonify, request, render_template_string
from app import db
from app.models.hotel import Hotel
from app.models.user import SystemUser
from app.models.location import Location
from app.models.buggy import Buggy
from app.models.request import BuggyRequest
from app.models.audit import AuditTrail
from app.models.session import Session
from app.middleware.setup_check import mark_setup_completed
from datetime import datetime
import os

system_reset_bp = Blueprint('system_reset', __name__)

# Secret password for system reset
RESET_PASSWORD = "518518Erkan"


@system_reset_bp.route('/buggysystemreset', methods=['GET'])
def system_reset_page():
    """System reset page"""
    html_template = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistem Sıfırlama - Buggy Call</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #667eea;
                font-size: 28px;
                margin-bottom: 10px;
            }
            
            .header .warning-icon {
                font-size: 60px;
                color: #f44336;
                margin-bottom: 20px;
            }
            
            .warning-box {
                background: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .warning-box h3 {
                color: #856404;
                margin-bottom: 10px;
                font-size: 18px;
            }
            
            .warning-box p {
                color: #856404;
                line-height: 1.6;
            }
            
            .stats-box {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .stats-box h3 {
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }
            
            .stat-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #dee2e6;
            }
            
            .stat-item:last-child {
                border-bottom: none;
            }
            
            .stat-label {
                color: #666;
                font-weight: 500;
            }
            
            .stat-value {
                color: #f44336;
                font-weight: bold;
                font-size: 18px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                color: #333;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 30px;
            }
            
            .btn {
                flex: 1;
                padding: 15px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn-check {
                background: #667eea;
                color: white;
            }
            
            .btn-check:hover {
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-reset {
                background: #f44336;
                color: white;
                display: none;
            }
            
            .btn-reset:hover {
                background: #d32f2f;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4);
            }
            
            .btn-cancel {
                background: #6c757d;
                color: white;
            }
            
            .btn-cancel:hover {
                background: #5a6268;
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .error-message {
                background: #f8d7da;
                color: #721c24;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }
            
            .success-message {
                background: #d4edda;
                color: #155724;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="warning-icon">⚠️</div>
                <h1>Sistem Sıfırlama</h1>
            </div>
            
            <div class="warning-box">
                <h3>🚨 DİKKAT: GERİ DÖNÜŞÜ OLMAYAN İŞLEM</h3>
                <p>Bu işlem tüm sistem verilerini kalıcı olarak silecektir. Bu işlem geri alınamaz!</p>
            </div>
            
            <div id="statsBox" class="stats-box">
                <h3>📊 Silinecek Veriler</h3>
                <div class="stat-item">
                    <span class="stat-label">Oteller</span>
                    <span class="stat-value" id="hotelCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Kullanıcılar</span>
                    <span class="stat-value" id="userCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Lokasyonlar</span>
                    <span class="stat-value" id="locationCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Buggy'ler</span>
                    <span class="stat-value" id="buggyCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Talepler</span>
                    <span class="stat-value" id="requestCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Denetim Kayıtları</span>
                    <span class="stat-value" id="auditCount">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Oturumlar</span>
                    <span class="stat-value" id="sessionCount">-</span>
                </div>
            </div>
            
            <div id="errorMessage" class="error-message"></div>
            <div id="successMessage" class="success-message"></div>
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>İşlem yapılıyor...</p>
            </div>
            
            <div id="formContainer">
                <div class="form-group">
                    <label for="password">Şifre</label>
                    <input type="password" id="password" placeholder="Sistem sıfırlama şifresini girin">
                </div>
                
                <div class="button-group">
                    <button class="btn btn-check" onclick="checkPassword()">Verileri Kontrol Et</button>
                    <button class="btn btn-cancel" onclick="window.location.href='/'">İptal</button>
                </div>
                
                <div class="button-group" style="margin-top: 10px;">
                    <button id="resetBtn" class="btn btn-reset" onclick="confirmReset()">
                        🗑️ SİSTEMİ SIFIRLA
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            let statsLoaded = false;
            
            async function checkPassword() {
                const password = document.getElementById('password').value;
                const errorMsg = document.getElementById('errorMessage');
                const loading = document.getElementById('loading');
                
                if (!password) {
                    showError('Lütfen şifre girin');
                    return;
                }
                
                errorMsg.style.display = 'none';
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/api/system-reset/check', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ password })
                    });
                    
                    const data = await response.json();
                    loading.style.display = 'none';
                    
                    if (response.ok) {
                        // Load stats
                        document.getElementById('hotelCount').textContent = data.stats.hotels;
                        document.getElementById('userCount').textContent = data.stats.users;
                        document.getElementById('locationCount').textContent = data.stats.locations;
                        document.getElementById('buggyCount').textContent = data.stats.buggies;
                        document.getElementById('requestCount').textContent = data.stats.requests;
                        document.getElementById('auditCount').textContent = data.stats.audit_logs;
                        document.getElementById('sessionCount').textContent = data.stats.sessions;
                        
                        // Show reset button
                        document.getElementById('resetBtn').style.display = 'block';
                        statsLoaded = true;
                        
                        showSuccess('Şifre doğru! Verileri kontrol ettiniz. Sıfırlama için butona tıklayın.');
                    } else {
                        showError(data.error || 'Şifre hatalı!');
                    }
                } catch (error) {
                    loading.style.display = 'none';
                    showError('Bir hata oluştu: ' + error.message);
                }
            }
            
            async function confirmReset() {
                if (!statsLoaded) {
                    showError('Önce şifreyi kontrol edin');
                    return;
                }
                
                const confirmed = confirm(
                    '⚠️ SON UYARI ⚠️\\n\\n' +
                    'TÜM VERİLER SİLİNECEK!\\n\\n' +
                    'Bu işlem geri alınamaz. Devam etmek istediğinizden emin misiniz?'
                );
                
                if (!confirmed) return;
                
                const doubleConfirm = confirm(
                    '🚨 TEKRAR ONAY 🚨\\n\\n' +
                    'Gerçekten tüm verileri silmek ve sistemi sıfırlamak istiyor musunuz?\\n\\n' +
                    'Bu işlem GERİ ALINAMAZ!'
                );
                
                if (!doubleConfirm) return;
                
                const password = document.getElementById('password').value;
                const loading = document.getElementById('loading');
                const formContainer = document.getElementById('formContainer');
                
                formContainer.style.display = 'none';
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/api/system-reset/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ password })
                    });
                    
                    const data = await response.json();
                    loading.style.display = 'none';
                    
                    if (response.ok) {
                        showSuccess('✅ Sistem başarıyla sıfırlandı! Kurulum ekranına yönlendiriliyorsunuz...');
                        setTimeout(() => {
                            window.location.href = '/setup';
                        }, 2000);
                    } else {
                        formContainer.style.display = 'block';
                        showError(data.error || 'Sıfırlama başarısız!');
                    }
                } catch (error) {
                    loading.style.display = 'none';
                    formContainer.style.display = 'block';
                    showError('Bir hata oluştu: ' + error.message);
                }
            }
            
            function showError(message) {
                const errorMsg = document.getElementById('errorMessage');
                errorMsg.textContent = message;
                errorMsg.style.display = 'block';
                document.getElementById('successMessage').style.display = 'none';
            }
            
            function showSuccess(message) {
                const successMsg = document.getElementById('successMessage');
                successMsg.textContent = message;
                successMsg.style.display = 'block';
                document.getElementById('errorMessage').style.display = 'none';
            }
            
            // Enter key support
            document.getElementById('password').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    checkPassword();
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)


@system_reset_bp.route('/api/system-reset/check', methods=['POST'])
def check_reset_password():
    """Check password and return data statistics"""
    try:
        from app.services.audit_service import AuditService
        
        data = request.get_json()
        password = data.get('password')
        
        if password != RESET_PASSWORD:
            # Log failed attempt
            AuditService.log_action(
                action='system_reset_password_failed',
                entity_type='system',
                new_values={'ip_address': request.remote_addr}
            )
            return jsonify({'error': 'Şifre hatalı!'}), 401
        
        # Get statistics
        stats = {
            'hotels': Hotel.query.count(),
            'users': SystemUser.query.count(),
            'locations': Location.query.count(),
            'buggies': Buggy.query.count(),
            'requests': BuggyRequest.query.count(),
            'audit_logs': AuditTrail.query.count(),
            'sessions': Session.query.count()
        }
        
        # Log successful password check
        AuditService.log_action(
            action='system_reset_password_verified',
            entity_type='system',
            new_values={
                'ip_address': request.remote_addr,
                'stats': stats
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Şifre doğru',
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@system_reset_bp.route('/api/system-reset/execute', methods=['POST'])
def execute_system_reset():
    """Execute system reset - DELETE ALL DATA"""
    try:
        from app.services.audit_service import AuditService
        
        data = request.get_json()
        password = data.get('password')
        
        if password != RESET_PASSWORD:
            # Log failed attempt
            AuditService.log_action(
                action='system_reset_execution_failed',
                entity_type='system',
                new_values={'ip_address': request.remote_addr, 'reason': 'invalid_password'}
            )
            return jsonify({'error': 'Şifre hatalı!'}), 401
        
        # Get statistics before deletion for audit log
        stats_before_deletion = {
            'hotels': Hotel.query.count(),
            'users': SystemUser.query.count(),
            'locations': Location.query.count(),
            'buggies': Buggy.query.count(),
            'requests': BuggyRequest.query.count(),
            'audit_logs': AuditTrail.query.count(),
            'sessions': Session.query.count()
        }
        
        # Log system reset BEFORE deletion
        AuditService.log_action(
            action='system_reset_executed',
            entity_type='system',
            new_values={
                'ip_address': request.remote_addr,
                'deleted_data': stats_before_deletion,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Commit audit log before deletion
        db.session.commit()
        
        # Delete all data in correct order (respecting foreign keys)
        Session.query.delete()
        AuditTrail.query.delete()
        BuggyRequest.query.delete()
        Buggy.query.delete()
        Location.query.delete()
        SystemUser.query.delete()
        Hotel.query.delete()
        
        db.session.commit()
        
        # Remove setup marker to return to setup wizard
        setup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.setup_completed')
        if os.path.exists(setup_file):
            os.remove(setup_file)
        
        return jsonify({
            'success': True,
            'message': 'Sistem başarıyla sıfırlandı',
            'redirect': '/setup'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
