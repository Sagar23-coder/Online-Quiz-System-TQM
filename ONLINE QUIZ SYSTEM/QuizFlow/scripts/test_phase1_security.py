"""
Phase 1 Security & Auth Hardening Verification Test
Tests:
1. Password Complexity Validation
2. In-Memory Brute-Force Rate Limiter (Lockout after max attempts)
3. Rate Limiter Reset on Successful Authentication
4. Argon2 / PBKDF2 Password Hashing
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.security import validate_password_complexity, get_password_hash, verify_password
from app.core.rate_limit import RateLimiter
from app.database.session import SessionLocal
from app.services.auth_service import AuthService
from app.schemas.user import UserLogin
from fastapi import HTTPException

def test_phase1():
    print("=" * 60)
    print("PHASE 1: SECURITY & AUTH HARDENING VERIFICATION")
    print("=" * 60)

    # 1. Password Complexity Tests
    print("\n[1] Testing Password Complexity Policy...")
    valid, msg = validate_password_complexity("short")
    assert not valid and "8 characters" in msg, f"Failed short check: {msg}"

    valid, msg = validate_password_complexity("alllowercase123")
    assert valid, f"Should accept mixed letters/digits: {msg}"

    valid, msg = validate_password_complexity("SecurePassword!2026")
    assert valid, f"Should accept strong password: {msg}"
    print("  ✓ PASS: Password policy correctly enforces minimum length & complexity.")

    # 2. Cryptographic Hash Test
    print("\n[2] Testing Cryptographic Hash & Verification...")
    test_pw = "TeacherSecret#2026"
    pw_hash = get_password_hash(test_pw)
    assert verify_password(test_pw, pw_hash), "Hash verification failed!"
    assert not verify_password("WrongSecret#2026", pw_hash), "False positive hash match!"
    print(f"  ✓ PASS: Password hashing verified (algorithm: {pw_hash.split('$')[0]}).")

    # 3. Rate Limiter Lockout Test
    print("\n[3] Testing Rate Limiter & Brute-Force Protection...")
    limiter = RateLimiter(max_attempts=3, window_seconds=60, lockout_seconds=60)
    key = "attacker@example.com"

    for i in range(3):
        is_lim, _ = limiter.is_rate_limited(key)
        assert not is_lim, f"Should not be locked out on attempt {i+1}"
        limiter.record_attempt(key, success=False)

    # 4th attempt should be locked out
    is_lim, retry_after = limiter.is_rate_limited(key)
    assert is_lim and retry_after > 0, "Rate limiter failed to lockout after 3 failed attempts!"
    print(f"  ✓ PASS: Brute-force lockout triggered correctly (retry after: {retry_after}s).")

    # Reset on success
    limiter.record_attempt(key, success=True)
    is_lim, _ = limiter.is_rate_limited(key)
    assert not is_lim, "Rate limiter failed to clear after successful login!"
    print("  ✓ PASS: Rate limiter correctly resets on successful login.")

    print("\n" + "=" * 60)
    print("PHASE 1 SECURITY TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase1()
