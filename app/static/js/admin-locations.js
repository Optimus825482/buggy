// Admin Locations JavaScript
async function loadLocations() {
    try {
        const response = await fetch('/api/locations');
        const data = await response.json();
        
        console.log('admin-locations.js - API Response:', data);
        
        // Parse locations from different response formats
        let locations = [];
        if (data.locations) {
            locations = data.locations;
        } else if (data.data && data.data.items) {
            locations = data.data.items;
        } else if (data.items) {
            locations = data.items;
        }
        
        console.log('admin-locations.js - Parsed locations:', locations);
        
        const locationsList = document.getElementById('locationsList');
        if (locations && locations.length > 0) {
            locationsList.innerHTML = `
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #1BA5A8, #0EA5E9); color: white;">
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px; width: 80px;">Sıra</th>
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px;">Lokasyon Adı</th>
                            <th style="padding: 16px; text-align: left; font-weight: 600; font-size: 14px;">Açıklama</th>
                            <th style="padding: 16px; text-align: center; font-weight: 600; font-size: 14px; width: 100px;">QR Kod</th>
                            <th style="padding: 16px; text-align: center; font-weight: 600; font-size: 14px; width: 100px;">Durum</th>
                            <th style="padding: 16px; text-align: center; font-weight: 600; font-size: 14px; width: 200px;">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${locations.map((loc, index) => `
                            <tr style="border-bottom: 1px solid #F3F4F6; cursor: pointer; transition: background 0.2s;" 
                                onmouseover="this.style.background='#F9FAFB'" 
                                onmouseout="this.style.background='white'"
                                onclick="showLocationDetails(${loc.id})">
                                <td style="padding: 16px;">
                                    <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                                        <div style="width: 45px; height: 45px; border-radius: 50%; background: linear-gradient(135deg, #1BA5A8, #0EA5E9); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 2px 8px rgba(27, 165, 168, 0.3);">
                                            ${loc.display_order || 0}
                                        </div>
                                        ${loc.display_order === 0 ? '<span style="font-size: 10px; color: #9CA3AF; font-weight: 500;"><i class="fas fa-magic"></i> Otomatik</span>' : ''}
                                    </div>
                                </td>
                                <td style="padding: 16px;">
                                    <div style="font-weight: 600; color: #1F2937; font-size: 15px;">${loc.name}</div>
                                </td>
                                <td style="padding: 16px;">
                                    <div style="color: #6B7280; font-size: 14px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                        ${loc.description || '-'}
                                    </div>
                                </td>
                                <td style="padding: 16px; text-align: center;">
                                    ${loc.qr_code_image ? `
                                        <img src="${loc.qr_code_image}" alt="QR" style="width: 50px; height: 50px; border-radius: 8px; border: 2px solid #E5E7EB;">
                                    ` : '<span style="color: #9CA3AF;">-</span>'}
                                </td>
                                <td style="padding: 16px; text-align: center;">
                                    <span style="padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; ${loc.is_active ? 'background: #D1FAE5; color: #065F46;' : 'background: #F3F4F6; color: #6B7280;'}">
                                        ${loc.is_active ? '✓ Aktif' : '○ Pasif'}
                                    </span>
                                </td>
                                <td style="padding: 16px; text-align: center;" onclick="event.stopPropagation();">
                                    <div style="display: flex; gap: 8px; justify-content: center;">
                                        <button onclick="editLocation(${loc.id})" 
                                                style="padding: 8px 16px; font-size: 13px; display: flex; align-items: center; gap: 6px; border-radius: 8px; background: #F59E0B; color: white; border: none; cursor: pointer; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);"
                                                onmouseover="this.style.background='#D97706'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(245, 158, 11, 0.4)'" 
                                                onmouseout="this.style.background='#F59E0B'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(245, 158, 11, 0.3)'"
                                                title="Düzenle">
                                            <i class="fas fa-edit"></i>
                                            Düzenle
                                        </button>
                                        <button onclick="deleteLocation(${loc.id}, '${loc.name.replace(/'/g, "\\'")}')" 
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
            locationsList.innerHTML = '<p style="text-align: center; color: #6B7280; padding: 3rem; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">Henüz lokasyon yok</p>';
        }
    } catch (error) {
        console.error('Failed to load locations:', error);
        document.getElementById('locationsList').innerHTML = '<p style="text-align: center; color: #E74C3C; grid-column: 1/-1;">Yüklenemedi</p>';
    }
}

// Show location details in modal
async function showLocationDetails(locationId) {
    try {
        console.log('Fetching location details for ID:', locationId);
        const response = await fetch(`/api/locations/${locationId}`);
        const data = await response.json();
        console.log('Location details response:', data);
        
        // Parse location from different response formats
        let loc = null;
        if (data.location) {
            loc = data.location;
        } else if (data.data && data.data.location) {
            loc = data.data.location;
        } else if (data.id) {
            // Response is the location itself
            loc = data;
        }
        
        console.log('Parsed location:', loc);
        
        if (!loc) {
            await BuggyModal.error('Lokasyon bulunamadı');
            return;
        }
        
        const detailsHtml = `
            <div style="text-align: center;">
                <h3 style="color: #1BA5A8; margin-bottom: 1rem;">${loc.name}</h3>
                ${loc.qr_code_image ? `
                    <div style="margin: 1rem auto; padding: 1rem; background: white; display: inline-block; border: 2px solid #ddd; border-radius: 8px;">
                        <img src="${loc.qr_code_image}" alt="QR Code" style="width: 200px; height: 200px;">
                        <p style="margin-top: 0.5rem; font-size: 12px; color: #666;">QR Kod</p>
                    </div>
                ` : ''}
                <div style="text-align: left; margin-top: 1rem; padding: 1rem; background: #F9FAFB; border-radius: 8px;">
                    <p><strong>Açıklama:</strong> ${loc.description || '-'}</p>
                    <p><strong>Sıra No:</strong> ${loc.display_order || 0}</p>
                    <p><strong>Durum:</strong> <span class="badge ${loc.is_active ? 'badge-success' : 'badge-secondary'}">${loc.is_active ? 'Aktif' : 'Pasif'}</span></p>
                    <p><strong>QR Kod URL:</strong><br><code style="font-size: 11px; word-break: break-all;">${loc.qr_code_data || '-'}</code></p>
                </div>
            </div>
        `;
        
        await BuggyModal.custom(detailsHtml, {
            title: 'Lokasyon Detayları',
            confirmText: 'Kapat',
            showCancel: false,
            size: 'medium'
        });
    } catch (error) {
        console.error('Failed to load location details:', error);
        await BuggyModal.error('Lokasyon detayları yüklenemedi');
    }
}

// Edit location
async function editLocation(locationId) {
    try {
        console.log('Fetching location for edit, ID:', locationId);
        const response = await fetch(`/api/locations/${locationId}`);
        const data = await response.json();
        console.log('Edit location response:', data);
        
        // Parse location from different response formats
        let loc = null;
        if (data.location) {
            loc = data.location;
        } else if (data.data && data.data.location) {
            loc = data.data.location;
        } else if (data.id) {
            // Response is the location itself
            loc = data;
        }
        
        console.log('Parsed location for edit:', loc);
        
        if (!loc) {
            await BuggyModal.error('Lokasyon bulunamadı');
            return;
        }
        
        const formHtml = `
            <form id="location-edit-form" style="text-align: left;">
                <div class="form-group">
                    <label class="form-label">Lokasyon Adı *</label>
                    <input type="text" name="name" class="form-control" value="${loc.name}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Açıklama</label>
                    <textarea name="description" class="form-control" rows="3">${loc.description || ''}</textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Sıra Numarası</label>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="number" id="edit_display_order_input" name="display_order" class="form-control" value="${loc.display_order || 0}" min="0" style="flex: 1;">
                        <button type="button" onclick="document.getElementById('edit_display_order_input').value = 0" 
                                style="padding: 8px 12px; background: #6B7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; white-space: nowrap;"
                                title="Otomatik sıra">
                            <i class="fas fa-magic"></i> Otomatik
                        </button>
                    </div>
                    <small class="form-text text-muted">
                        <i class="fas fa-info-circle"></i> 0 = Sistem otomatik sıra atar | Manuel: 1, 2, 3... (Küçük numara önce gösterilir)
                    </small>
                </div>
                <div class="form-check">
                    <input type="checkbox" name="is_active" class="form-check-input" id="edit_is_active" ${loc.is_active ? 'checked' : ''}>
                    <label class="form-check-label" for="edit_is_active">Aktif</label>
                </div>
            </form>
        `;
        
        const confirmed = await BuggyModal.custom(formHtml, {
            title: 'Lokasyon Düzenle',
            confirmText: 'Güncelle',
            cancelText: 'İptal',
            size: 'medium'
        });
        
        if (confirmed) {
            const form = document.getElementById('location-edit-form');
            const formData = new FormData(form);
            const updateData = {
                name: formData.get('name'),
                description: formData.get('description'),
                display_order: parseInt(formData.get('display_order')) || 0,
                is_active: formData.get('is_active') === 'on'
            };
            
            console.log('Updating location:', updateData);
            const updateResponse = await fetch(`/api/locations/${locationId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
            
            const result = await updateResponse.json();
            console.log('Update response:', result);
            
            if (updateResponse.ok) {
                await BuggyModal.success('Lokasyon başarıyla güncellendi!');
                loadLocations();
            } else {
                await BuggyModal.error(result.error || 'Lokasyon güncellenemedi');
            }
        }
    } catch (error) {
        console.error('Failed to edit location:', error);
        await BuggyModal.error('Bir hata oluştu: ' + error.message);
    }
}

// Delete location
async function deleteLocation(locationId, locationName) {
    const confirmed = await BuggyModal.confirm(
        `"${locationName}" lokasyonunu silmek istediğinize emin misiniz? Bu işlem geri alınamaz.`,
        'Lokasyonu Sil',
        'Evet, Sil',
        'İptal'
    );
    
    if (confirmed) {
        try {
            console.log('Deleting location:', locationId);
            const response = await fetch(`/api/locations/${locationId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            console.log('Delete response:', result);
            
            if (response.ok) {
                await BuggyModal.success('Lokasyon başarıyla silindi!');
                loadLocations();
            } else {
                await BuggyModal.error(result.error || 'Lokasyon silinemedi');
            }
        } catch (error) {
            console.error('Failed to delete location:', error);
            await BuggyModal.error('Bir hata oluştu: ' + error.message);
        }
    }
}

function showAddLocationModal() {
    // Show simple form modal
    const formHtml = `
        <form id="location-form-inline" style="text-align: left;">
            <div class="form-group">
                <label class="form-label">Lokasyon Adı *</label>
                <input type="text" name="name" class="form-control" required placeholder="Örn: Havuz, Plaj, Restaurant">
            </div>
            <div class="form-group">
                <label class="form-label">Açıklama</label>
                <textarea name="description" class="form-control" rows="3" placeholder="Lokasyon hakkında kısa açıklama..."></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Sıra Numarası</label>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input type="number" id="display_order_input" name="display_order" class="form-control" value="0" min="0" style="flex: 1;">
                    <button type="button" onclick="document.getElementById('display_order_input').value = 0" 
                            style="padding: 8px 12px; background: #6B7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; white-space: nowrap;"
                            title="Otomatik sıra">
                        <i class="fas fa-magic"></i> Otomatik
                    </button>
                </div>
                <small class="form-text text-muted">
                    <i class="fas fa-info-circle"></i> 0 = Sistem otomatik sıra atar | Manuel: 1, 2, 3... (Küçük numara önce gösterilir)
                </small>
            </div>
            <div class="form-check">
                <input type="checkbox" name="is_active" class="form-check-input" id="is_active" checked>
                <label class="form-check-label" for="is_active">Aktif</label>
            </div>
        </form>
    `;
        
    BuggyModal.custom(formHtml, {
        title: 'Yeni Lokasyon Ekle',
        confirmText: 'Kaydet',
        cancelText: 'İptal',
        size: 'medium'
    }).then(async (confirmed) => {
        if (confirmed) {
            const form = document.getElementById('location-form-inline');
            const formData = new FormData(form);
            const displayOrder = parseInt(formData.get('display_order')) || 0;
            
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                display_order: displayOrder,
                is_active: formData.get('is_active') === 'on'
            };
            
            try {
                console.log('Creating location with data:', data);
                const response = await fetch('/api/locations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                console.log('Create location response:', result);
                
                if (response.ok) {
                    await BuggyModal.success('Lokasyon başarıyla eklendi!');
                    loadLocations();
                } else {
                    await BuggyModal.error(result.error || 'Lokasyon eklenemedi');
                }
            } catch (error) {
                console.error('Create location error:', error);
                await BuggyModal.error('Bir hata oluştu: ' + error.message);
            }
        }
    });
}

loadLocations();
