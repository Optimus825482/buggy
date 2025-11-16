"""
Migration: Update completion_time calculation
Recalculate completion_time as (completed_at - requested_at) instead of (completed_at - accepted_at)
"""
from app import db
from app.models.request import BuggyRequest, RequestStatus
from datetime import datetime


def update_completion_times():
    """
    Mevcut tamamlanmış taleplerin completion_time değerlerini yeniden hesapla
    """
    print("🔄 Completion time güncelleme başlıyor...")
    
    # Tamamlanmış tüm talepleri al
    completed_requests = BuggyRequest.query.filter(
        BuggyRequest.status == RequestStatus.COMPLETED,
        BuggyRequest.completed_at.isnot(None),
        BuggyRequest.requested_at.isnot(None)
    ).all()
    
    print(f"📊 Toplam {len(completed_requests)} tamamlanmış talep bulundu")
    
    updated_count = 0
    error_count = 0
    
    for req in completed_requests:
        try:
            # Yeni hesaplama: requested_at -> completed_at (TOPLAM SÜRE)
            old_value = req.completion_time
            delta = req.completed_at - req.requested_at
            new_value = int(delta.total_seconds())
            
            if old_value != new_value:
                req.completion_time = new_value
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"✅ {updated_count} talep güncellendi...")
                    db.session.commit()
            
        except Exception as e:
            error_count += 1
            print(f"❌ Request {req.id} güncellenemedi: {str(e)}")
    
    # Son commit
    db.session.commit()
    
    print(f"\n✅ Güncelleme tamamlandı!")
    print(f"📊 Güncellenen: {updated_count}")
    print(f"❌ Hata: {error_count}")
    print(f"📈 Toplam: {len(completed_requests)}")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    
    with app.app_context():
        confirm = input("⚠️ Tüm completion_time değerleri güncellenecek. Devam edilsin mi? (yes/no): ")
        if confirm.lower() == 'yes':
            update_completion_times()
        else:
            print("❌ İşlem iptal edildi")
