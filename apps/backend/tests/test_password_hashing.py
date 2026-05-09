"""Tests for password hashing and verification helpers."""

from taskmaster_backend.identity.passwords import hash_password, verify_password


def test_hash_password_returns_non_plaintext_scrypt_hash() -> None:
    password = "CorrectHorseBatteryStaple!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("scrypt$")


def test_same_password_produces_distinct_hashes() -> None:
    password = "CorrectHorseBatteryStaple!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


def test_verify_password_returns_false_for_incorrect_password() -> None:
    password_hash = hash_password("CorrectHorseBatteryStaple!")

    assert verify_password("Tr0ub4dor&3", password_hash) is False


def test_verify_password_returns_false_for_invalid_hash_format() -> None:
    assert verify_password("CorrectHorseBatteryStaple!", "not-a-valid-hash") is False
