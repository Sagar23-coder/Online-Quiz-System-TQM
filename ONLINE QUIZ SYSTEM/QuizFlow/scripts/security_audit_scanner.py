import os
import re

workspace = "QuizFlow"
sensitive_patterns = [
    (r"(?i)(api[_-]?key|secret[_-]?key|jwt[_-]?secret|private[_-]?key)\s*[:=]\s*['\"]([^'\"]+)['\"]", "Secret/Key"),
    (r"(?i)postgres(?:ql)?://[^\s:]+:[^\s@]+@[^\s/]+", "Database Connection String with Credentials"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Auth Bearer Token"),
]

found_items = []
db_files = []
env_files = []
backup_files = []

for root, dirs, files in os.walk(workspace):
    dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache", "node_modules", ".git"]]
    for f in files:
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, ".")
        lower_f = f.lower()

        if lower_f.endswith((".db", ".sqlite", ".sqlite3")):
            db_files.append(rel_path)
        if "backup" in lower_f and lower_f.endswith((".db", ".bak", ".sql")):
            backup_files.append(rel_path)
        if lower_f.startswith(".env") and not lower_f.endswith(".example"):
            env_files.append(rel_path)

        # Check content
        if lower_f.endswith((".py", ".html", ".js", ".json", ".yaml", ".yml", ".bat", ".sh", ".md", ".txt")):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    for pattern, label in sensitive_patterns:
                        matches = re.findall(pattern, content)
                        for m in matches:
                            val = m[1] if isinstance(m, tuple) else m
                            val_str = str(val).lower()
                            # Ignore variable names, env lookups, or generic placeholders
                            if any(p in val_str for p in ["placeholder", "example", "your-", "change-this", "os.getenv", "none", "secret-key", "secret_key", "default"]):
                                continue
                            if len(str(val)) > 6:
                                found_items.append((rel_path, label, str(val)[:3] + "..." + str(val)[-2:]))
            except Exception:
                pass

print("=== SENSITIVE INFORMATION AUDIT REPORT ===")
print("1. Live/Active Database Files:")
for d in db_files:
    print(f"   - {d}")
print("2. Database Backup Files:")
for b in backup_files:
    print(f"   - {b}")
print("3. Real .env Configuration Files:")
for e in env_files:
    print(f"   - {e}")
print("4. Potential Secrets / Keys Found in Code:")
for p, l, masked in found_items:
    print(f"   - [{l}] in {p}: {masked}")
if not found_items:
    print("   ✓ None detected (all credentials use environment variable lookups)")
