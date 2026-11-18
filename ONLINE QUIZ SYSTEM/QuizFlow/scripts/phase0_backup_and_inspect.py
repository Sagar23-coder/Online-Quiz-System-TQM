import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

db_path = Path(r"c:\Users\Asus\ONLINE QUIZ SYSTEM\QuizFlow\backend\quizflow.db")
if not db_path.exists():
    print(f"Error: {db_path} does not exist!")
    exit(1)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = db_path.parent / f"quizflow_backup_phase0_{timestamp}.db"
shutil.copyfile(db_path, backup_path)
print(f"BACKUP CREATED: {backup_path}")
print(f"FILE SIZE: {os.path.getsize(backup_path)} bytes")

con = sqlite3.connect(backup_path)
cur = con.cursor()
tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
print(f"TOTAL TABLES: {len(tables)}")
for t in sorted(tables):
    cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    cols = [col[1] for col in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"  * {t}: {cnt} rows | cols: {cols}")
con.close()
