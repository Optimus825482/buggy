"""
Alembic migration çalıştırma helper script
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
    
    # Komut: upgrade head (en son migration'a kadar)
    command = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    target = sys.argv[2] if len(sys.argv) > 2 else "head"
    
    print(f"🔄 Migration çalıştırılıyor: {command} {target}")
    print(f"📁 Dizin: {app_dir}")
    
    # Alembic komutunu çalıştır
    cmd = ["alembic", command, target]
    
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
        print("✅ Migration başarıyla çalıştırıldı!")
    else:
        print("❌ Migration çalıştırma hatası!")
        sys.exit(1)
