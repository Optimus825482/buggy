"""
Fix Request Status Case - Lowercase to Uppercase
DB'deki lowercase status değerlerini uppercase'e çevir
"""
from app import create_app, db

app = create_app()

def fix_request_status_case():
    """DB'deki request status değerlerini uppercase'e çevir"""
    with app.app_context():
        try:
            print("🔄 Request status değerleri güncelleniyor...")
            
            # Lowercase -> Uppercase mapping
            status_mapping = {
                'PENDING': 'PENDING',
                'accepted': 'ACCEPTED',
                'completed': 'COMPLETED',
                'cancelled': 'CANCELLED',
                'unanswered': 'UNANSWERED'
            }
            
            # Her status için güncelleme
            total_updated = 0
            for old_status, new_status in status_mapping.items():
                result = db.session.execute(
                    db.text(
                        "UPDATE buggy_requests SET status = :new_status "
                        "WHERE status = :old_status"
                    ),
                    {'old_status': old_status, 'new_status': new_status}
                )
                updated = result.rowcount
                if updated > 0:
                    print(f"  ✅ {old_status} -> {new_status}: {updated} kayıt güncellendi")
                    total_updated += updated
            
            db.session.commit()
            
            print(f"\n✅ Toplam {total_updated} kayıt güncellendi!")
            
            # Kontrol et
            result = db.session.execute(
                db.text("SELECT DISTINCT status FROM buggy_requests")
            ).fetchall()
            
            print(f"\n📊 Güncel status değerleri: {[r[0] for r in result]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("REQUEST STATUS CASE FIX")
    print("=" * 60)
    
    success = fix_request_status_case()
    
    if success:
        print("\n✅ İşlem başarılı!")
    else:
        print("\n❌ İşlem başarısız!")
