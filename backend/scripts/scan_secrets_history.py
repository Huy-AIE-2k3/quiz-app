"""Git History & Repository Secret Scanner (TC-0.2-05).

Scans git commit history and tracked files for private keys, live database passwords,
and sensitive cloud tokens.
"""

import re
import subprocess
import sys

# High-risk patterns for actual cloud credentials & secret keys
# Regex strings are composed to avoid false alarms during pre-commit self-checks
PATTERNS = [
    (
        r"(?i)" + "aws_" + r"secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{20,}['\"]",
        "AWS/R2 Secret Key",
    ),
    (
        r"postgresql://[^:\s]+:[^@\s]+@(?!127\.0\.0\.1|localhost)[^\s/]+/[^\s]+",
        "Live External PostgreSQL URL with Password",
    ),
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----", "Private Key"),
    (r"(?i)ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"(?i)neon_api_[A-Za-z0-9_]{20,}", "Neon API Key"),
]


def scan_git_history() -> int:
    """Scans all git commits for sensitive patterns."""
    print("[TC-0.2-05] Quét lịch sử Git kiểm tra rò rỉ bí mật đám mây...")
    log_cmd = ["git", "log", "-p", "--all"]
    proc = subprocess.run(log_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print("Lỗi khi đọc lịch sử git:", proc.stderr)
        return 1

    diff_text = proc.stdout
    findings = 0

    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_content = line[1:].strip()
            # Ignore test mocks, examples, regex patterns, and placeholders
            if any(
                skip in added_content.lower()
                for skip in (
                    "mock",
                    "example",
                    "your_",
                    "change_this",
                    "user:pass",
                    "ep-xyz",
                    "r\"postgresql",
                )
            ):
                continue

            for pattern, name in PATTERNS:
                if re.search(pattern, added_content):
                    print(f"  ❌ Phát hiện mẫu nhạy cảm ({name}): {added_content[:60]}...")
                    findings += 1

    if findings == 0:
        print("  ✅ Không phát hiện bí mật đám mây nào trong toàn bộ lịch sử Git (0 vi phạm)!")
        return 0
    else:
        print(f"  ⚠️ Cảnh báo: Tìm thấy {findings} vi phạm!")
        return 1


if __name__ == "__main__":
    sys.exit(scan_git_history())
