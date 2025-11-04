#!/usr/bin/env python3
"""
Frontend'de Buggy -> Shuttle değişikliği
Sadece kullanıcıya görünen metinleri değiştirir
Backend kodu dokunulmaz
"""
import os
import re
from pathlib import Path

# Değişiklik kuralları
REPLACEMENTS = {
    # Türkçe metinler
    'Buggy Çağır': 'Shuttle Çağır',
    'Buggy çağır': 'Shuttle çağır',
    'Buggy çağrılıyor': 'Shuttle çağrılıyor',
    'Buggy çağrısı': 'Shuttle çağrısı',
    'Buggy çağrınız': 'Shuttle çağrınız',
    'Buggy Yolda': 'Shuttle Yolda',
    'Buggy yolda': 'Shuttle yolda',
    'Buggy Call': 'Shuttle Call',
    'Buggy\'niz': 'Shuttle\'iniz',
    'Buggy\'niz': 'Shuttle\'iniz',
    'Buggy ulaştı': 'Shuttle ulaştı',
    'Buggy Kabul Edildi': 'Shuttle Kabul Edildi',
    'buggy çağırabilirsiniz': 'shuttle çağırabilirsiniz',
    'buggy tarafından': 'shuttle tarafından',
    'buggy yönlendirilecek': 'shuttle yönlendirilecek',
    'Buggy:': 'Shuttle:',
    'buggy atanmamış': 'shuttle atanmamış',
    'bir buggy': 'bir shuttle',
    'Yeni Buggy Talebi': 'Yeni Shuttle Talebi',
    
    # İngilizce metinler (yorumlarda vs)
    'Buggy Call System': 'Shuttle Call System',
    'Buggy Call Logo': 'Shuttle Call Logo',
    'Buggy Call -': 'Shuttle Call -',
}

# Değiştirilmeyecek dosyalar (backend)
EXCLUDE_PATTERNS = [
    'app/models/',
    'app/routes/',
    'app/services/',
    'migrations/',
    'tests/',
    '.py',  # Python dosyaları hariç (sadece frontend)
]

# Değiştirilecek dosya tipleri
INCLUDE_EXTENSIONS = ['.html', '.js', '.css']

def should_process_file(file_path):
    """Dosyanın işlenmesi gerekip gerekmediğini kontrol et"""
    file_str = str(file_path)
    
    # Hariç tutulanları kontrol et
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_str:
            return False
    
    # Uzantıyı kontrol et
    return any(file_path.suffix == ext for ext in INCLUDE_EXTENSIONS)

def replace_in_file(file_path):
    """Dosyadaki metinleri değiştir"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Her değişikliği uygula
        for old_text, new_text in REPLACEMENTS.items():
            if old_text in content:
                count = content.count(old_text)
                content = content.replace(old_text, new_text)
                changes_made.append(f"  - '{old_text}' -> '{new_text}' ({count}x)")
        
        # Değişiklik varsa kaydet
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"\n✅ {file_path}")
            for change in changes_made:
                print(change)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Hata ({file_path}): {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🔄 Buggy -> Shuttle Değişikliği (Frontend Only)")
    print("=" * 60)
    
    # Çalışma dizini
    base_dir = Path('.')
    
    # İşlenecek klasörler
    folders_to_process = [
        'templates',
        'app/static/js',
        'app/static/css',
    ]
    
    total_files = 0
    changed_files = 0
    
    for folder in folders_to_process:
        folder_path = base_dir / folder
        if not folder_path.exists():
            print(f"⚠️  Klasör bulunamadı: {folder}")
            continue
        
        print(f"\n📁 İşleniyor: {folder}")
        
        # Tüm dosyaları tara
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and should_process_file(file_path):
                total_files += 1
                if replace_in_file(file_path):
                    changed_files += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Tamamlandı!")
    print(f"📊 Toplam dosya: {total_files}")
    print(f"📝 Değiştirilen: {changed_files}")
    print("=" * 60)

if __name__ == '__main__':
    main()
