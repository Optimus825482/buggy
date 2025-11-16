"""
Alembic migration oluşturma helper script
"""
import sys
import os
from pathlib import Path

# Backend-api dizinini path'e ekle
backend_api_path = Path(__file__).parent
sys.path.insert(0, str(backend_api_path))

# .env dosyasını yükle
from dotenv import load_dotenv
load_dotenv(backend_api_path / ".env")

# Alembic komutunu çalıştır
if __name__ == "__main__":
    import subprocess
    
    # app dizinine geç
    app_dir = backend_api_path / "app"
    
    # Migration mesajını al
    message = sys.argv[1] if len(sys.argv) > 1 else "initial_migration"
    
    print(f"🔄 Migration oluşturuluyor: {message}")
    print(f"📁 Dizin: {app_dir}")
    
    # Alembic revision komutunu çalıştır
    cmd = ["alembic", "revision", "--autogenerate", "-m", message]
    
    result = subprocess.run(
        cmd,
        cwd=str(app_dir),
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode == 0:
        print("✅ Migration başarıyla oluşturuldu!")
    else:
        print("❌ Migration oluşturma hatası!")
        sys.exit(1)
