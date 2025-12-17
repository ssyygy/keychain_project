import json
import os
import secrets
import string 

CHARSET_FILE = "charset.txt"
USERS_FILE = "users.json"

def load_charset():
    if not os.path.exists(CHARSET_FILE):
        default_charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        with open(CHARSET_FILE, "w", encoding="utf-8") as f:
            f.write(default_charset)
    with open(CHARSET_FILE, "r", encoding="utf-8") as f:
        charset = f.read().strip()
    return charset

CHARSET = load_charset()

def caesar_cipher(text: str, shift: int, decrypt=False) -> str:
    """
    Функция шифрования/расшифровки строки с использованием шифра Цезаря.

    Функция выполняет сдвиг символов входной строки по заданному набору
    символов. Может использоваться как для шифрования, так и для
    расшифровки данных в зависимости от значения параметра decrypt.

    :param text: Входная строка для шифрования или расшифровки
    :type text: str
    :param shift: Величина сдвига символов
    :type shift: int
    :param decrypt: Флаг расшифровки (True — расшифровка, False — шифрование)
    :type decrypt: bool
    :returns: Cтрока-результат после шифрования или расшифровки
    :rtype: str
    """
    if not text:
        return text
    direction = -1 if decrypt else 1
    result = []
    for char in text:
        if char in CHARSET:
            idx = CHARSET.index(char)
            new_idx = (idx + direction * shift) % len(CHARSET)
            result.append(CHARSET[new_idx])
        else:
            result.append(char)
    return ''.join(result)

def load_users():
    if not os.path.exists(USERS_FILE): 
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_account():
    users = load_users()
    while True:
        login_name = input("Введите логин: ").strip()
        if not login_name:
            print("Логин не может быть пустым.")
            continue
        if login_name in users:
            print("Аккаунт с таким логином уже существует.")
            retry = input("Попробовать другой логин? (y/n): ").strip().lower()
            if retry != 'y':
                return None
        else:
            break

    while True:
        master = input("Введите мастер-пароль (минимум 6 символов): ")
        if len(master) < 6:
            print("Слишком короткий пароль.")
            continue
        confirm = input("Подтвердите мастер-пароль: ")
        if master != confirm:
            print("Пароли не совпадают.")
            continue
        break

    users[login_name] = {
        "master_password": master,
        "passwords": {},
        "custom_categories": []
    }
    save_users(users)
    print("Аккаунт создан успешно!")
    print(f"Автоматический вход выполнен как {login_name}!")
    return login_name

def login():
    users = load_users()
    if not users:
        print("Нет аккаунтов. Создайте первый.")
        create_now = input("Создать аккаунт сейчас? (y/n): ").strip().lower()
        if create_now == 'y':
            login_name = create_account()
            if login_name:
                user_session(login_name, users)
        return

    login_name = input("Логин: ").strip()
    if login_name not in users:
        print("Пользователь не найден.")
        create_now = input(f"Создать аккаунт '{login_name}'? (y/n): ").strip().lower()
        if create_now == 'y':
            login_name = create_account()
            if login_name:
                user_session(login_name, users)
        return

    for tries in range(3):
        master = input("Мастер-пароль: ")
        if master == users[login_name]["master_password"]:
            print("Вход выполнен!")
            user_session(login_name, users)
            return
        else:
            if 2-tries==1: print(f"Неверный пароль. У вас осталось 1 попытка!")
            elif 2-tries==2: print(f"Неверный пароль. У вас осталось 2 попытки!")
    print("\n"+"Слишком много попыток!")

def select_category(login_name: str, users: dict) -> str:
    print("\n" + "="*30)
    print("Выберите категорию:")
    print("="*30)
    
    standard_categories = get_categories()
    print("Стандартные категории:")
    for i, category in enumerate(standard_categories, 1):
        print(f"{i}. {category}")
    
    custom_categories = users[login_name].get("custom_categories", [])
    if custom_categories:
        print("\nВаши категории:")
        for i, category in enumerate(custom_categories, len(standard_categories) + 1):
            print(f"{i}. {category}")
    
    print(f"{len(standard_categories) + len(custom_categories) + 1}. Создать новую категорию")
    print("="*30)
    
    while True:
        choice = input("Выберите номер категории: ").strip()
        if choice.isdigit():
            choice_num = int(choice)
            total_standard = len(standard_categories)
            total_categories = total_standard + len(custom_categories)
            
            if 1 <= choice_num <= total_standard:
                return standard_categories[choice_num - 1]
            elif total_standard < choice_num <= total_categories:
                return custom_categories[choice_num - total_standard - 1]
            elif choice_num == total_categories + 1:
                return create_new_category(login_name, users)
        
        print("Неверный выбор. Попробуйте снова.")

def show_passwords_by_category(login_name: str, users: dict):

    all_categories = get_categories() + users[login_name].get("custom_categories", [])
    if not all_categories:
        print("Нет доступных категорий.")
        return
    
    print("\nДоступные категории:")
    for i, category in enumerate(all_categories, 1):
        print(f"{i}. {category}")
    
    choice = input("\nВыберите номер категории: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(all_categories)):
        print("Неверный выбор.")
        return
    
    selected_category = all_categories[int(choice) - 1]
    passwords = users[login_name]["passwords"]

    filtered = [(r, d) for r, d in passwords.items() if d.get("category") == selected_category]
    
    if not filtered:
        print(f"В категории '{selected_category}' нет паролей.")
        return
    
    print(f"\nПароли в категории '{selected_category}':")
    print("="*40)
    for resource, data in sorted(filtered, key=lambda x: x[0]):
        shift = len(data["encrypted"])
        decrypted = caesar_cipher(data["encrypted"], shift, decrypt=True)
        print(f"{resource}: {decrypted}")
    print(f"\nВсего в категории: {len(filtered)}")

def search_passwords(login_name: str, users: dict):
    search_term = input("Введите часть названия ресурса: ").strip().lower()
    if not search_term:
        print("Пустой поисковый запрос.")
        return
    
    passwords = users[login_name]["passwords"]
    found = []
    
    for resource, data in passwords.items():
        if search_term in resource.lower():
            found.append((resource, data))
    
    if not found:
        print("Ничего не найдено.")
        return
    
    print(f"\nРезультаты поиска '{search_term}':")
    print("="*40)
    for resource, data in sorted(found, key=lambda x: x[0]):
        shift = len(data["encrypted"])
        decrypted = caesar_cipher(data["encrypted"], shift, decrypt=True)
        category = data.get("category", "Без категории")
        print(f"{resource} [{category}]: {decrypted}")
    print(f"\nНайдено: {len(found)}")

#ДАШАААА
def get_categories():
    return [
        "Соцсети",
        "Банки/Финансы", 
        "Работа/Бизнес",
        "Электронная почта",
        "Образование",
        "Развлечения",
        "Магазины/Покупки",
        "Здоровье/Медицина",
        "Государственные услуги",
        "Другое"
    ]

def main_menu():
    print("\n" + "="*40)
    print("Добро пожаловать в менеджер паролей mykeychain!")
    print("="*40)
    print("1. Создать аккаунт")
    print("2. Войти")
    print("3. Выход")
    print("="*40)

def user_menu():
    print("\n" + "-"*40)
    print("1. Добавить пароль")
    print("2. Изменить пароль")
    print("3. Удалить пароль")
    print("4. Сгенерировать пароль")
    print("5. Показать все пароли")
    print("6. Показать пароли по категории")
    print("7. Поиск паролей")
    print("8. Выйти из аккаунта")
    print("-"*40)

def main():
    while True:
        main_menu()
        choice = input("Выберите действие: ").strip()
        if choice == "1":
            login_name = create_account()
            if login_name:
                users = load_users()
                user_session(login_name, users)
        elif choice == "2":
            login()
        elif choice == "3":
            print("Выход.")
            break
        else:
            print("Неверный выбор.")

def user_session(login_name: str, users: dict):
    while True:
        user_menu()
        choice = input("Выбор: ").strip()
        if choice == "1":
            add_password(login_name, users)
        elif choice == "2":
            update_password(login_name, users)
        elif choice == "3":
            delete_password(login_name, users)
        elif choice == "4":
            generate_and_show_password()
        elif choice == "5":
            show_all_passwords(login_name, users)
        elif choice == "6":
            show_passwords_by_category(login_name, users)
        elif choice == "7":
            search_passwords(login_name, users)
        elif choice == "8":
            save_users(users)
            print("Вы вышли из аккаунта.")
            break
        else:
            print("Неверный выбор.")

def generate_password(length=12, use_digits=True, use_special=True):
    """
    Функция генерации случайного пароля.

    Функция создаёт пароль заданной длины с использованием букв
    латинского алфавита. По желанию пользователя в пароль могут быть
    включены цифры и специальные символы. Для генерации используется криптографически стойкий генератор
    случайных чисел.

    :param length: Длина генерируемого пароля
    :type length: int
    :param use_digits: Флаг использования цифр в пароле
    :type use_digits: bool
    :param use_special: Флаг использования специальных символов в пароле
    :type use_special: bool
    :returns: Сгенерированный пароль
    :rtype: str
    """
    chars = string.ascii_letters
    if use_digits:
        chars += string.digits
    if use_special:
        chars += "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def create_new_category(login_name: str, users: dict) -> str:
    while True:
        new_category = input("Введите название новой категории: ").strip()
        if not new_category:
            print("Название не может быть пустым.")
            continue
        
        all_categories = get_categories() + users[login_name].get("custom_categories", [])
        if new_category in all_categories:
            print("Такая категория уже существует.")
            continue
        
        if "custom_categories" not in users[login_name]:
            users[login_name]["custom_categories"] = []
        users[login_name]["custom_categories"].append(new_category)
        save_users(users)
        print(f"Категория '{new_category}' создана!")
        return new_category

def add_password(login_name: str, users: dict):
    """
    Функция добавления нового пароля для пользователя.

    Функция запрашивает у пользователя название ресурса и пароль.
    Если пароль не введён, он автоматически генерируется.
    Перед сохранением пароль шифруется с использованием шифра Цезаря.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    """
    resource = input("Название ресурса: ").strip()
    if not resource:
        print("\n"+"Ресурс не может быть пустым.")
        return
    if resource in users[login_name]["passwords"]:
        print("\n"+"Пароль для этого ресурса уже существует.")
        return

    category = select_category(login_name, users)
    
    password = input("Пароль (оставьте пустым для генерации): ")
    if not password:
        password = generate_and_show_password(auto=True)

    shift = len(password)
    encrypted = caesar_cipher(password, shift)
    
    users[login_name]["passwords"][resource] = {
        "encrypted": encrypted,
        "category": category
    }
    
    print("Пароль добавлен.")

def update_password(login_name: str, users: dict):
    resource = input("Название ресурса: ").strip()
    if not resource:
        print("\n"+"Ресурс не может быть пустым.")
        return
    if resource not in users[login_name]["passwords"]:
        print("\n"+"Ресурс не найден.")
        return

    password = input("Новый пароль (оставьте пустым для генерации): ")
    if not password:
        password = generate_and_show_password(auto=True)

    shift = len(password)
    encrypted = caesar_cipher(password, shift)
    
    old_category = users[login_name]["passwords"][resource]["category"]
    
    users[login_name]["passwords"][resource] = {
        "encrypted": encrypted,
        "category": old_category
    }
    print("Пароль обновлён.")

def delete_password(login_name: str, users: dict):
    resource = input("Название ресурса: ").strip()
    if not resource:
        print("\n"+"Ресурс не может быть пустым.")
        return
    if resource not in users[login_name]["passwords"]:
        print("\n"+"Ресурс не найден.")
        return

    confirm = input(f"Удалить пароль для '{resource}'? (y/n): ").strip().lower()
    if confirm == "y":
        del users[login_name]["passwords"][resource]
        print("Пароль удалён.")
    else:
        print("Удаление отменено.")

def generate_and_show_password(auto=False):
    length = input("Длина пароля (минимальная длина 4, по умолчанию 12): ").strip()
    length = int(length) if length.isdigit() else 12
    if length < 4:
        length = 12
    use_digits = input("Использовать цифры? (y/n, по умолчанию y): ").strip().lower() != "n"
    use_special = input("Использовать спецсимволы? (y/n, по умолчанию y): ").strip().lower() != "n"

    pwd = generate_password(length, use_digits, use_special)
    if not auto:
        print(f"Сгенерированный пароль: {pwd}")
    return pwd

def show_all_passwords(login_name: str, users: dict):
    passwords = users[login_name]["passwords"]
    if not passwords:
        print("Список паролей пуст.")
        return
    
    print("\n" + "="*60)
    print("ВСЕ СОХРАНЕННЫЕ ПАРОЛИ")
    print("="*60)
    
    categories = {}
    for resource, data in passwords.items():
        category = data.get("category", "Без категории")
        if category not in categories:
            categories[category] = []
        categories[category].append((resource, data))
    
    for category, items in sorted(categories.items()):
        print(f"\n[{category.upper()}]")
        print("-" * 40)
        for resource, data in sorted(items, key=lambda x: x[0]):
            shift = len(data["encrypted"])
            decrypted = caesar_cipher(data["encrypted"], shift, decrypt=True)
            print(f"{resource}: {decrypted}")
    
    print("\n" + "="*60)
    print(f"Всего паролей: {len(passwords)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход по запросу пользователя.")