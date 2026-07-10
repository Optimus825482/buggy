"""
Local MariaDB'den Coolify MySQL'e veri aktarım scripti
Kullanım: docker exec -i <app_container> python scripts/import_local_data.py
"""
import pymysql
import os
from datetime import datetime

# Local DB (export kaynağı)
LOCAL_HOST = "host.docker.internal"  # Docker host
LOCAL_PORT = 3306
LOCAL_USER = "erkan"
LOCAL_PASS = "518518Erkan"
LOCAL_DB = "buggycalldb"

try:
    conn = pymysql.connect(
        host=LOCAL_HOST, port=LOCAL_PORT,
        user=LOCAL_USER, password=LOCAL_PASS,
        database=LOCAL_DB, charset='utf8mb4'
    )
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # Prod DB (Coolify)
    prod_host = os.getenv('DB_HOST', 'mysql')
    prod_port = int(os.getenv('DB_PORT', 3306))
    prod_user = os.getenv('DB_USER', 'shuttlecall_user')
    prod_pass = os.getenv('DB_PASSWORD', '')
    prod_db = os.getenv('DB_NAME', 'shuttlecall')

    prod_conn = pymysql.connect(
        host=prod_host, port=prod_port,
        user=prod_user, password=prod_pass,
        database=prod_db, charset='utf8mb4'
    )
    prod_cur = prod_conn.cursor()

    # Tabloları sırayla aktar
    tables = ['hotels', 'system_users', 'locations', 'buggies', 
              'buggy_drivers', 'buggy_requests', 'audit_trail', 
              'sessions', 'notification_logs']

    for table in tables:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        if not rows:
            print(f"  {table}: 0 satır (atlandı)")
            continue

        # Kolon isimlerini al
        columns = list(rows[0].keys())
        # guest_device_id varsa çıkar (model'de yok)
        if 'guest_device_id' in columns:
            columns.remove('guest_device_id')

        placeholders = ','.join(['%s'] * len(columns))
        col_names = ','.join(columns)
        insert_sql = f"INSERT IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"

        for row in rows:
            values = [row.get(col) for col in columns]
            try:
                prod_cur.execute(insert_sql, values)
            except Exception as e:
                print(f"  HATA: {table} ID={row.get('id')}: {e}")
                prod_conn.rollback()
                break

        prod_conn.commit()
        print(f"  ✅ {table}: {len(rows)} satır aktarıldı")

    print("\n✅ Tüm veriler aktarıldı!")
    conn.close()
    prod_conn.close()

except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
