

import pytest
from unittest.mock import*
from mykeychain import*

@pytest.fixture
def mock_users():
    return {
        "alice": {
            "passwords": {
                "google.com": {"encrypted": "KHOOR", "category": "Соцсети"},
                "github.com": {"encrypted": "KHOOR", "category": "Работа/Бизнес"},
            },
            "custom_categories": []
        }
    }

def test_caesar_cipher_encrypt_and_decrypt_roundtrip():
    original = "Test123!"
    shift = 10
    encrypted = caesar_cipher(original, shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == original

def test_caesar_cipher_empty_string():
    assert caesar_cipher("", 5) == ""

def test_caesar_cipher_non_charset_chars_unchanged():
    text = "Привет"
    assert caesar_cipher(text, 100) == text

def test_caesar_cipher_zero_shift():
    text = "abc123"
    assert caesar_cipher(text, 0) == text

def test_caesar_cipher_negative_shift():
    text = "bcd"
    assert caesar_cipher(text, -1) == "abc"

def test_caesar_cipher_large_shift():
    text = "a"
    shift = 10000
    encrypted = caesar_cipher(text, shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == "a"

def test_caesar_cipher_encrypt_and_decrypt():
    text = "hello"
    shift = 3
    encrypted = caesar_cipher(text, shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == text

def test_caesar_cipher_non_charset_unchanged():
    assert caesar_cipher("a!b", 1) != caesar_cipher("a", 1) + "!" + caesar_cipher("b", 1)


def test_load_users_file_not_exists():
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)
    assert load_users() == {}

def test_load_users_valid_json():
    data = {"user": {"master_password": "pass", "passwords": {}}}
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        assert load_users() == data
    finally:
        os.remove(USERS_FILE)

def test_load_users_empty_file_raises():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        pass
    try:
        with pytest.raises(json.JSONDecodeError):
            load_users()
    finally:
        os.remove(USERS_FILE)

def test_load_users_invalid_json_raises():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        f.write("{ invalid json ]")
    try:
        with pytest.raises(json.JSONDecodeError):
            load_users()
    finally:
        os.remove(USERS_FILE)

def test_load_users_file_with_null_bytes():
    with open(USERS_FILE, "wb") as f:
        f.write(b'\x00{"key": "value"}')
    try:
        with pytest.raises(json.JSONDecodeError):
            load_users()
    finally:
        os.remove(USERS_FILE)

def test_save_users_creates_file():
    data = {"test": {"x": 1}}
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)
    try:
        save_users(data)
        assert os.path.exists(USERS_FILE)
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            assert json.load(f) == data
    finally:
        if os.path.exists(USERS_FILE):
            os.remove(USERS_FILE)

def test_save_users_overwrites_file():
    save_users({"a": 1})
    save_users({"b": 2})
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        assert json.load(f) == {"b": 2}
    os.remove(USERS_FILE)

def test_save_users_non_serializable_data():
    users = {"key": set([1, 2, 3])}
    with pytest.raises(TypeError):
        save_users(users)
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)

def test_save_users_empty_dict():
    save_users({})
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            assert json.load(f) == {}
    finally:
        os.remove(USERS_FILE)






def test_get_categories_returns_list():
    result = get_categories()
    assert isinstance(result, list)

def test_get_categories_has_expected_length():
    assert len(get_categories()) == 10

def test_get_categories_contains_key_items():
    cats = get_categories()
    assert "Соцсети" in cats
    assert "Банки/Финансы" in cats
    assert "Другое" in cats

def test_get_categories_is_immutable_across_calls():
    cats1 = get_categories()
    cats2 = get_categories()
    assert cats1 is not cats2
    cats1.append("Test")
    assert "Test" not in get_categories()

def test_get_categories_no_empty_strings():
    for cat in get_categories():
        assert isinstance(cat, str)
        assert cat.strip() != ""
        assert cat == cat.strip()


def test_generate_password_default_length():
    pwd = generate_password()
    assert len(pwd) == 12

def test_generate_password_custom_length():
    pwd = generate_password(8)
    assert len(pwd) == 8

def test_generate_password_with_digits_and_special():
    pwd = generate_password()
    has_letter = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_special = any(c in "!@#$%^&*" for c in pwd)
    assert has_letter
    assert has_digit or has_special

def test_generate_password_no_digits_no_special():
    pwd = generate_password(length=10, use_digits=False, use_special=False)
    assert pwd.isalpha()
    assert len(pwd) == 10

def test_generate_password_length_zero():
    pwd = generate_password(0)
    assert pwd == ""

def test_generate_password_negative_length():
    pwd = generate_password(-5)
    assert pwd == ""


@pytest.fixture
def mock_users_empty():
    return {"alice": {"passwords": {}, "custom_categories": []}}

@pytest.fixture
def mock_users_with_google():
    return {"alice": {"passwords": {"google.com": {"encrypted": "...", "category": "Соцсети"}}, "custom_categories": []}}

@patch("mykeychain.select_category", return_value="Соцсети")
@patch("mykeychain.generate_and_show_password", return_value="mypassword123")
@patch("builtins.input", side_effect=["example.com", ""])
@patch("builtins.print")
def test_add_password_success(mock_print, mock_input, mock_gen, mock_select, mock_users_empty):
    add_password("alice", mock_users_empty)
    assert "example.com" in mock_users_empty["alice"]["passwords"]
    mock_print.assert_called_with("Пароль добавлен.")

@patch("builtins.input", return_value="")
@patch("builtins.print")
def test_add_password_empty_resource(mock_print, mock_input, mock_users_empty):
    with pytest.raises(InvalidInputError, match="не может быть пустым"):
        add_password("alice", mock_users_empty)

@patch("builtins.input", return_value="google.com")
@patch("builtins.print")
def test_add_password_resource_already_exists(mock_print, mock_input, mock_users_with_google):
    with pytest.raises(ResourceExistsError, match="уже существует"):
        add_password("alice", mock_users_with_google)
