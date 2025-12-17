import os
import json

from mykeychain import caesar_cipher, generate_password, load_users, save_users, load_charset
def test_caesar_cipher_encrypt_decrypt(): #1
    shift = len("test")
    encrypted = caesar_cipher("test", shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == "test"

def test_caesar_cipher_empty_string(): 
    assert caesar_cipher("", 5) == ""

def test_caesar_cipher_unknown_chars():
    text = "пароль"
    result = caesar_cipher(text, 3)
    assert result == text

def test_generate_password_default_length():
    password = generate_password()
    assert len(password) == 12

def test_generate_password_custom_length():
    password = generate_password(20)
    assert len(password) == 20

def test_generate_password_only_letters():
    password = generate_password(15, use_digits=False, use_special=False)
    assert password.isalpha()

def test_generate_password_contains_digits_when_enabled():
    password = generate_password(30, use_digits=True, use_special=False)
    assert any(char.isdigit() for char in password)

def test_generate_password_contains_special_when_enabled():
    password = generate_password(30, use_digits=False, use_special=True)
    assert any(char in "!@#$%^&*" for char in password)

def test_password_encryption_logic():
    password = "MyStrongPass!"
    shift = len(password)
    encrypted = caesar_cipher(password, shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == password

def test_different_passwords_encrypt_differently():
    e1 = caesar_cipher("password1", len("password1"))
    e2 = caesar_cipher("password2", len("password2"))
    assert e1 != e2
