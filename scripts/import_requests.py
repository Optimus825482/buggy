"""
Buggy_requests import script - handles guest_device_id column removal
"""
import pymysql
import re

with open('/app/export_buggycall.sql', 'r') as f:
    sql = f.read()

conn = pymysql.connect(
    host='mysql', port=3306,
    user='shuttlecall_user', password='shuttlecall_pass',
    database='shuttlecall', charset='utf8mb4'
)
cur = conn.cursor()

# Find all buggy_requests INSERT statements
pattern = r"INSERT INTO `buggy_requests` \((.*?)\) VALUES (.*?);"
for match in re.finditer(pattern, sql, re.DOTALL):
    cols_str = match.group(1)
    values_str = match.group(2)

    cols = [c.strip().strip('`') for c in cols_str.split(',')]

    # Remove guest_device_id
    if 'guest_device_id' in cols:
        gd_idx = cols.index('guest_device_id')
        cols.pop(gd_idx)
    else:
        gd_idx = -1

    # Parse individual rows from VALUES (...),(...),...
    rows = []
    depth = 0
    current = ''
    for ch in values_str:
        if ch == '(':
            depth += 1
            if depth == 1:
                current = ''
                continue
        elif ch == ')':
            depth -= 1
            if depth == 0:
                rows.append(current)
                continue
        if depth >= 1:
            current += ch

    inserted = 0
    for row_text in rows:
        # Parse comma-separated values respecting quotes
        vals = []
        cur = ''
        in_str = False
        for ch in row_text:
            if ch == "'" and (not cur or cur[-1] != '\\'):
                in_str = not in_str
            if ch == ',' and not in_str:
                vals.append(cur)
                cur = ''
            else:
                cur += ch
        if cur:
            vals.append(cur)

        # Remove guest_device_id value
        if gd_idx >= 0 and len(vals) > gd_idx:
            vals.pop(gd_idx)

        cols_sql = ','.join(cols)
        placeholders = ','.join(['%s'] * len(vals))
        insert_sql = f"INSERT IGNORE INTO buggy_requests ({cols_sql}) VALUES ({placeholders})"

        try:
            cur.execute(insert_sql, vals)
            inserted += 1
        except Exception as e:
            print(f"SKIP: {e}")

    conn.commit()
    print(f"✅ buggy_requests: {inserted} satir aktarildi")

cur.close()
conn.close()
