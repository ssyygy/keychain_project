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

def test_caesar_cipher_encrypt_and_decrypt():
    text = "hello"
    shift = 3
    encrypted = caesar_cipher(text, shift)
    decrypted = caesar_cipher(encrypted, shift, decrypt=True)
    assert decrypted == text

def test_caesar_cipher_empty():
    assert caesar_cipher("", 5) == ""

def test_caesar_cipher_non_charset_unchanged():
    assert caesar_cipher("a!b", 1) != caesar_cipher("a", 1) + "!" + caesar_cipher("b", 1)


@patch("mykeychain.caesar_cipher", return_value="hello")
@patch("builtins.print")
@patch("builtins.input", return_value="goo")
def test_search_passwords_found(mock_input, mock_print, mock_cipher, mock_users):
    search_passwords("alice", mock_users)
    printed = str(mock_print.call_args_list)
    assert "google.com" in printed
    assert "Найдено: 1" in printed

@patch("builtins.print")
@patch("builtins.input", return_value="")
def test_search_passwords_empty(mock_input, mock_print, mock_users):
    search_passwords("alice", mock_users)
    mock_print.assert_called_with("Пустой поисковый запрос.")

@patch("builtins.print")
@patch("builtins.input", return_value="xyz")
def test_search_passwords_not_found(mock_input, mock_print, mock_users):
    search_passwords("alice", mock_users)
    mock_print.assert_called_with("Ничего не найдено.")


@patch("mykeychain.get_categories", return_value=["Соцсети", "Банки/Финансы"])
@patch("mykeychain.caesar_cipher", return_value="hello")
@patch("builtins.print")
@patch("builtins.input", return_value="1")
def test_show_passwords_by_category_found(mock_input, mock_print, mock_cipher, mock_get, mock_users):
    show_passwords_by_category("alice", mock_users)
    printed = str(mock_print.call_args_list)
    assert "google.com: hello" in printed

@patch("mykeychain.get_categories", return_value=["Соцсети"])
@patch("builtins.print")
@patch("builtins.input", return_value="999")
def test_show_passwords_by_category_invalid_choice(mock_input, mock_print, mock_get, mock_users):
    show_passwords_by_category("alice", mock_users)
    mock_print.assert_any_call("Неверный выбор.")


def test_generate_password_default():
    pwd = generate_password()
    assert len(pwd) == 12
    assert pwd.isalnum() or any(c in "!@#$%^&*" for c in pwd)

def test_generate_password_no_special():
    pwd = generate_password(use_special=False)
    assert not any(c in "!@#$%^&*" for c in pwd)

def test_generate_password_length():
    pwd = generate_password(8)
    assert len(pwd) == 8


@patch("mykeychain.get_categories", return_value=["Соцсети"])
@patch("mykeychain.save_users")
@patch("builtins.input", side_effect=["", "Личное"])
def test_create_new_category_skip_empty(mock_input, mock_save, mock_get, mock_users):
    result = create_new_category("alice", mock_users)
    assert result == "Личное"
    assert "Личное" in mock_users["alice"]["custom_categories"]

@patch("mykeychain.get_categories", return_value=["Соцсети"])
@patch("mykeychain.save_users")
@patch("builtins.input", side_effect=["Соцсети", "Новое"])
@patch("builtins.print")
def test_create_new_category_avoid_duplicate(mock_print, mock_input, mock_save, mock_get, mock_users):
    result = create_new_category("alice", mock_users)
    assert result == "Новое"
    assert mock_print.called


@patch("mykeychain.user_menu")
@patch("builtins.input", side_effect=["8"])
@patch("mykeychain.save_users")
def test_user_session_exit(mock_save, mock_input, mock_menu, mock_users):
    user_session("alice", mock_users)
    mock_save.assert_called_once()

@patch("mykeychain.user_menu")
@patch("builtins.input", side_effect=["5", "8"])
@patch("mykeychain.show_all_passwords")
@patch("mykeychain.save_users")
def test_user_session_show_all(mock_save, mock_show, mock_input, mock_menu, mock_users):
    user_session("alice", mock_users)
    mock_show.assert_called_once_with("alice", mock_users)

@patch("mykeychain.user_menu")
@patch("builtins.input", side_effect=["1", "8"])
@patch("mykeychain.add_password")
@patch("mykeychain.save_users")
def test_user_session_add_password(mock_save, mock_add, mock_input, mock_menu, mock_users):
    user_session("alice", mock_users)
    mock_add.assert_called_once_with("alice", mock_users)