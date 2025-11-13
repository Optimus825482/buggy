"""
Password Hash Generator for Shuttle Drivers
"""
from werkzeug.security import generate_password_hash

# Şifreler: isim + sıra numarası formatında
passwords = {
    'hasan': 'hasan045',
    'mehmet': 'mehmet056',
    'ozlem': 'ozlem067',
    'mustafao': 'mustafao078',
    'mohammad': 'mohammad089',
    'ferhan': 'ferhan0910',
    'ayla': 'ayla1011',
    'mustafab': 'mustafab1112',
    'fatma': 'fatma1213',
    'ahmet': 'ahmet1314'
}

print("=" * 80)
print("PASSWORD HASH GENERATOR - SHUTTLE DRIVERS")
print("=" * 80)
print()

for username, password in passwords.items():
    hash_value = generate_password_hash(password)
    print(f"{username}:{hash_value}")
    print()

print("=" * 80)
print("COMPLETED!")
print("=" * 80)
