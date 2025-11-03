// Admin Buggies JavaScript

const buggyStatusBadges = {
    'available': '<span class="badge badge-success">Müsait</span>',
    'busy': '<span class="badge badge-warning">Meşgul</span>',
    'offline': '<span class="badge badge-secondary">Çevrimdışı</span>'
};

async function loadBuggies() {
    try {
        const response = await fetch('/api/buggies');
        const data = await response.json();
        
        console.log('Buggies API response:', data);
        
        const buggiesList = document.getElementById('buggiesList');
        
        // Parse buggies from different response formats
        let buggies = [];
        if (data.buggies) {
            buggies = data.buggies;
        } else if (data.data && data.data.buggies) {
            buggies = data.data.buggies;
        }
        
        console.log('Parsed buggies:', buggies);
        
        if (buggies && buggies.length > 0) {
            buggiesList.innerHTML = `
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #1BA5A8, #0EA5E9); color: white;">
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px;">Buggy Kodu</th>
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px;">Plaka</th>
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px;">Sürücü</th>
                            <th style="padding: 16px; text-align: center; font-weight: 600; font-size: 14px; width: 120px;">Durum</th>
                            <th style="padding: 16px; text-align: center; font-weight: 600; font-size: 14px; width: 200px;">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${buggies.map(buggy => `
                            <tr style="border-bottom: 1px solid #F3F4F6; cursor: pointer; transition: background 0.2s;" 
                                onmouseover="this.style.background='#F9FAFB'" 
                                onmouseout="this.style.background='white'"
                                onclick="showBuggyDetails(${buggy.id})">
                                <td style="padding: 16px;">
                                    <div style="font-weight: 600; color: #1F2937; font-size: 15px;">
                                        🚗 ${buggy.code}
                                    </div>
                                </td>
                                <td style="padding: 16px;">
                                    <div style="color: #6B7280; font-size: 14px;">
                                        ${buggy.license_plate || '-'}
                                    </div>
                                </td>
                                <td style="padding: 16px;">
                                    <div style="color: #1F2937; font-size: 14px;">
                                        ${buggy.driver_name || '<span style="color: #9CA3AF;">Atanmadı</span>'}
                                    </div>
                                </td>
                                <td style="padding: 16px; text-align: center;">
                                    ${buggyStatusBadges[buggy.status] || buggy.status}
                                </td>
                                <td style="padding: 16px; text-align: center;" onclick="event.stopPropagation();">
                                    <div style="display: flex; gap: 8px; justify-content: center;">
                                        <button onclick="editBuggy(${buggy.id})" 
                                                style="padding: 8px 16px; font-size: 13px; display: flex; align-items: center; gap: 6px; border-radius: 8px; background: #F59E0B; color: white; border: none; cursor: pointer; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);"
                                                onmouseover="this.style.background='#D97706'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(245, 158, 11, 0.4)'" 
                                                onmouseout="this.style.background='#F59E0B'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(245, 158, 11, 0.3)'"
                                                title="Düzenle">
                                            <i class="fas fa-edit"></i>
                                            Düzenle
                                        </button>
                                        <button onclick="deleteBuggy(${buggy.id}, '${buggy.code.replace(/'/g, "\\'")}')" 
                                                style="padding: 8px 16px; font-size: 13px; display: flex; align-items: center; gap: 6px; border-radius: 8px; background: #EF4444; color: white; border: none; cursor: pointer; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);"
                                                onmouseover="this.style.background='#DC2626'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(239, 68, 68, 0.4)'" 
                                                onmouseout="this.style.background='#EF4444'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(239, 68, 68, 0.3)'"
                                                title="Sil">
                                            <i class="fas fa-trash"></i>
                                            Sil
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            buggiesList.innerHTML = '<p style="text-align: center; color: #6B7280; padding: 3rem; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">Henüz buggy yok</p>';
        }
    } catch (error) {
        console.error('Failed to load buggies:', error);
        document.getElementById('buggiesList').innerHTML = '<p style="text-align: center; color: #E74C3C;">Yüklenemedi</p>';
    }
}

function showAddBuggyModal() {
    // Check if Admin object exists (from admin.js)
    if (typeof Admin !== 'undefined' && Admin.showBuggyModal) {
        Admin.showBuggyModal();
    } else {
        // Fallback: Show simple form modal
        const formHtml = `
            <form id="buggy-form-inline" style="text-align: left;">
                <div class="form-group">
                    <label class="form-label">Buggy Kodu *</label>
                    <input type="text" name="code" class="form-control" placeholder="Örn: B01" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Plaka</label>
                    <input type="text" name="license_plate" class="form-control" placeholder="34 ABC 123">
                </div>
                <div style="background: #FEF3C7; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 2px solid #F59E0B;">
                    <h4 style="color: #92400E; margin-bottom: 0.5rem; font-size: 14px;">
                        <i class="fas fa-user"></i> Sürücü Bilgileri
                    </h4>
                    <div class="form-group">
                        <label class="form-label">Sürücü Kullanıcı Adı *</label>
                        <input type="text" name="driver_username" class="form-control" placeholder="Örn: ahmet" required style="text-transform: lowercase;">
                        <small class="form-text text-muted">
                            <i class="fas fa-info-circle"></i> Geçici şifre otomatik oluşturulacak: <strong>kullaniciadi123*</strong>
                        </small>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Sürücü Adı Soyadı *</label>
                        <input type="text" name="driver_full_name" class="form-control" placeholder="Örn: Ahmet Yılmaz" required>
                    </div>
                </div>
            </form>
        `;
        
        BuggyModal.custom(formHtml, {
            title: 'Yeni Buggy Ekle',
            confirmText: 'Kaydet',
            cancelText: 'İptal',
            size: 'medium'
        }).then(async (confirmed) => {
            if (confirmed) {
                const form = document.getElementById('buggy-form-inline');
                const formData = new FormData(form);
                const data = {
                    code: formData.get('code'),
                    license_plate: formData.get('license_plate'),
                    driver_username: formData.get('driver_username').trim().toLowerCase(),
                    driver_full_name: formData.get('driver_full_name')
                };
                
                try {
                    console.log('Creating buggy with data:', data);
                    const response = await fetch('/api/buggies', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    console.log('Create buggy response:', result);
                    
                    if (response.ok) {
                        // Show driver credentials
                        const driverInfo = result.driver;
                        const credentialsHtml = `
                            <div style="text-align: left; background: #F0FDF4; padding: 1.5rem; border-radius: 8px; border: 2px solid #10B981;">
                                <h3 style="color: #059669; margin-bottom: 1rem;">
                                    <i class="fas fa-check-circle"></i> Buggy ve Sürücü Oluşturuldu!
                                </h3>
                                <div style="background: white; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                                    <h4 style="color: #1F2937; margin-bottom: 0.5rem;">Buggy Bilgileri:</h4>
                                    <p><strong>Kod:</strong> ${result.buggy.code}</p>
                                    <p><strong>Plaka:</strong> ${result.buggy.license_plate || '-'}</p>
                                </div>
                                <div style="background: #FEF3C7; padding: 1rem; border-radius: 6px; border: 2px dashed #F59E0B;">
                                    <h4 style="color: #92400E; margin-bottom: 0.5rem;">
                                        <i class="fas fa-key"></i> Sürücü Giriş Bilgileri (Geçici Şifre)
                                    </h4>
                                    <p><strong>Kullanıcı Adı:</strong> <code style="background: white; padding: 4px 8px; border-radius: 4px; font-size: 16px;">${driverInfo.username}</code></p>
                                    <p><strong>Geçici Şifre:</strong> <code style="background: white; padding: 4px 8px; border-radius: 4px; font-size: 16px;">${driverInfo.temp_password}</code></p>
                                    <p style="margin-top: 1rem; color: #92400E; font-size: 14px;">
                                        <i class="fas fa-info-circle"></i> Sürücü ilk girişte yeni şifre belirlemek zorunda kalacak.
                                    </p>
                                    <p style="color: #92400E; font-size: 13px;">
                                        <i class="fas fa-exclamation-triangle"></i> Bu bilgileri sürücüye iletin!
                                    </p>
                                </div>
                            </div>
                        `;
                        
                        await BuggyModal.custom(credentialsHtml, {
                            title: 'Buggy Başarıyla Oluşturuldu',
                            confirmText: 'Anladım, Kapat',
                            showCancel: false,
                            size: 'medium'
                        });
                        
                        loadBuggies();
                    } else {
                        await BuggyModal.error(result.error || 'Buggy eklenemedi');
                    }
                } catch (error) {
                    console.error('Create buggy error:', error);
                    await BuggyModal.error('Bir hata oluştu: ' + error.message);
                }
            }
        });
    }
}

loadBuggies();


// Show buggy details in modal
async function showBuggyDetails(buggyId) {
    try {
        const response = await fetch(`/api/buggies/${buggyId}`);
        const data = await response.json();
        
        // Parse buggy from response
        let buggy = null;
        if (data.buggy) {
            buggy = data.buggy;
        } else if (data.data && data.data.buggy) {
            buggy = data.data.buggy;
        } else if (data.id) {
            buggy = data;
        }
        
        if (!buggy) {
            alert('Buggy bulunamadı');
            return;
        }
        
        const detailsHtml = `
            <div style="text-align: left;">
                <h3 style="color: #1BA5A8; margin-bottom: 1rem;">🚗 ${buggy.code}</h3>
                <div style="background: #F9FAFB; padding: 1rem; border-radius: 8px;">
                    <p><strong>Plaka:</strong> ${buggy.license_plate || '-'}</p>
                    <p><strong>Sürücü:</strong> ${buggy.driver_name || '-'}</p>
                    <p><strong>Durum:</strong> ${buggyStatusBadges[buggy.status] || buggy.status}</p>
                </div>
            </div>
        `;
        
        if (typeof BuggyModal !== 'undefined') {
            await BuggyModal.custom(detailsHtml, {
                title: 'Buggy Detayları',
                confirmText: 'Kapat',
                showCancel: false
            });
        } else {
            alert('Buggy ID: ' + buggyId);
        }
    } catch (error) {
        console.error('Failed to load buggy details:', error);
        alert('Buggy detayları yüklenemedi');
    }
}

// Edit buggy
async function editBuggy(buggyId) {
    try {
        const response = await fetch(`/api/buggies/${buggyId}`);
        const data = await response.json();
        
        // Parse buggy
        let buggy = null;
        if (data.buggy) {
            buggy = data.buggy;
        } else if (data.data && data.data.buggy) {
            buggy = data.data.buggy;
        } else if (data.id) {
            buggy = data;
        }
        
        if (!buggy) {
            await BuggyModal.error('Buggy bulunamadı');
            return;
        }
        
        const formHtml = `
            <form id="buggy-edit-form" style="text-align: left;">
                <div class="form-group">
                    <label class="form-label">Buggy Kodu *</label>
                    <input type="text" name="code" class="form-control" value="${buggy.code}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Plaka</label>
                    <input type="text" name="license_plate" class="form-control" value="${buggy.license_plate || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Durum</label>
                    <select name="status" class="form-control">
                        <option value="available" ${buggy.status === 'available' ? 'selected' : ''}>Müsait</option>
                        <option value="busy" ${buggy.status === 'busy' ? 'selected' : ''}>Meşgul</option>
                        <option value="offline" ${buggy.status === 'offline' ? 'selected' : ''}>Çevrimdışı</option>
                    </select>
                </div>
            </form>
        `;
        
        const confirmed = await BuggyModal.custom(formHtml, {
            title: 'Buggy Düzenle',
            confirmText: 'Güncelle',
            cancelText: 'İptal',
            size: 'medium'
        });
        
        if (confirmed) {
            const form = document.getElementById('buggy-edit-form');
            const formData = new FormData(form);
            const updateData = {
                code: formData.get('code'),
                license_plate: formData.get('license_plate'),
                status: formData.get('status')
            };
            
            console.log('Updating buggy:', updateData);
            const updateResponse = await fetch(`/api/buggies/${buggyId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
            
            const result = await updateResponse.json();
            console.log('Update response:', result);
            
            if (updateResponse.ok) {
                await BuggyModal.success('Buggy başarıyla güncellendi!');
                loadBuggies();
            } else {
                await BuggyModal.error(result.error || 'Buggy güncellenemedi');
            }
        }
    } catch (error) {
        console.error('Failed to edit buggy:', error);
        await BuggyModal.error('Bir hata oluştu: ' + error.message);
    }
}

// Delete buggy
async function deleteBuggy(buggyId, buggyCode) {
    const confirmed = await BuggyModal.confirm(
        `"${buggyCode}" buggy'sini silmek istediğinize emin misiniz? Bu işlem geri alınamaz.`,
        'Buggy Sil',
        'Evet, Sil',
        'İptal'
    );
    
    if (confirmed) {
        try {
            console.log('Deleting buggy:', buggyId);
            const response = await fetch(`/api/buggies/${buggyId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            console.log('Delete response:', result);
            
            if (response.ok) {
                await BuggyModal.success('Buggy başarıyla silindi!');
                loadBuggies();
            } else {
                await BuggyModal.error(result.error || 'Buggy silinemedi');
            }
        } catch (error) {
            console.error('Failed to delete buggy:', error);
            await BuggyModal.error('Bir hata oluştu: ' + error.message);
        }
    }
}
