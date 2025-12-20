import json
import os
import secrets
import string 
import getpass

class MyKeyChainError(Exception):
    """Класс для всех исключений"""
    pass

class UserExistsError(MyKeyChainError):
    """Попытка создать аккаунт с уже существующим логином"""
    pass

class UserNotFoundError(MyKeyChainError):
    """Пользователь не найден"""
    pass

class AuthenticationError(MyKeyChainError):
    """Ошибка аутентификации (неверный пароль)"""
    pass

class InvalidInputError(MyKeyChainError):
    """Некорректный ввод от пользователя (пустой логин, короткий пароль и т.д.)"""
    pass

class ResourceExistsError(MyKeyChainError):
    """Пароль для ресурса уже существует"""
    pass

class ResourceNotFoundError(MyKeyChainError):
    """Ресурс не найден при обновлении/удалении"""
    pass

CHARSET_FILE = "charset.txt"
"""
Имя файла, содержащего набор символов для шифрования и расшифровки паролей.

Файл содержит строку уникальных символов, по которой выполняется сдвиг
в шифре Цезаря. Если файл отсутствует при запуске программы, он создаётся автоматически.
"""

USERS_FILE = "users.json"
"""
Имя файла для хранения данных пользователей в формате JSON.

Данные включают: логин, мастер-пароль (в открытом виде!), зашифрованные пароли
и пользовательские категории. Файл создаётся автоматически при первом создании аккаунта.
"""

def load_charset():
    """
    Загружает набор символов из файла charset.txt.

    Если файл не существует, создаёт его с набором стандартных ASCII-символов.
    Файл используется для определения алфавита при шифровании/расшифровке
    с помощью шифра Цезаря.

    :returns: Строка, представляющая используемый набор символов
    :rtype: str
    """
    if not os.path.exists(CHARSET_FILE):
        default_charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        with open(CHARSET_FILE, "w", encoding="utf-8") as f:
            f.write(default_charset)
    with open(CHARSET_FILE, "r", encoding="utf-8") as f:
        charset = f.read().strip()
    return charset

CHARSET = load_charset()
"""
Глобальный набор символов, используемый для шифрования и расшифровки паролей.

Содержит все допустимые символы, по которым выполняется циклический сдвиг
в шифре Цезаря.
"""

def caesar_cipher(text: str, shift: int, decrypt=False) -> str:
    """
    Функция шифрования/расшифровки строки c использованием шифра Цезаря.

    Функция выполняет сдвиг символов входной строки по заданному набору
    символов. Может использоваться как для шифрования, так и для
    расшифровки данных в зависимости от значения параметра decrypt.

    :param text: Входная строка для шифрования или расшифровки
    :type text: str
    :param shift: Величина сдвига символов
    :type shift: int
    :param decrypt: Флаг расшифровки (True — расшифровка, False — шифрование)
    :type decrypt: bool
    :returns: Cтрокa-результат после шифрования или расшифровки
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
    """
    Загружает данные пользователей из файла users.json.

    Если файл не существует, возвращает пустой словарь.
    Данные хранятся в формате JSON и содержат мастер-пароли,
    зашифрованные пароли и пользовательские категории.

    :returns: Словарь пользователей, где ключ — логин, значение — данные аккаунта
    :rtype: dict
    """
    if not os.path.exists(USERS_FILE): 
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    """
    Сохраняет данные пользователей в файл users.json.

    Данные записываются в человекочитаемом формате с отступами (indent=2)
    и с поддержкой Unicode (ensure_ascii=False).

    :param users: Словарь пользователей для сохранения
    :type users: dict
    """
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_account():
    """
    Создаёт новый пользовательский аккаунт в системе.

    :returns: Логин созданного пользователя
    :rtype: str
    :raises UserExistsError: Если логин уже занят
    :raises InvalidInputError: При пустом логине или коротком/несовпадающем пароле
    """
    users = load_users()
    while True:
        login_name = input("Введите логин: ").strip()
        if not login_name:
            raise InvalidInputError("Логин не может быть пустым.")
        if login_name in users:
            raise UserExistsError(f"Аккаунт с логином '{login_name}' уже существует.")
        else:
            break

    while True:
        master = getpass.getpass("Введите мастер-пароль (минимум 6 символов): ")
        if len(master) < 6:
            raise InvalidInputError("Мастер-пароль должен содержать минимум 6 символов.")
        confirm = getpass.getpass("Подтвердите мастер-пароль: ")
        if master != confirm:
            raise InvalidInputError("Пароли не совпадают.")
        break

    users[login_name] = {
        "master_password": master,
        "passwords": {},
        "custom_categories": []
    }
    save_users(users)
    print("Аккаунт создан успешно!")
    return login_name

def login():
    """
    Выполняет аутентификацию пользователя по логину и мастер-паролю.

    Если аккаунты отсутствуют — предлагает создать первый.
    При вводе несуществующего логина — предлагает создать новый аккаунт.
    Разрешено до 3 попыток ввода пароля. При успешной аутентификации
    запускается пользовательская сессия.

    :raises UserNotFoundError: Если пользователь не найден и отказался от создания аккаунта
    :raises AuthenticationError: Если исчерпаны все попытки ввода пароля
    """
    users = load_users()
    if not users:
        print("Нет аккаунтов. Создайте первый.")
        create_now = input("Создать аккаунт сейчас? (y/n): ").strip().lower()
        if create_now == 'y':
            login_name = create_account()
            user_session(login_name, load_users())
            return
        else:
            raise UserNotFoundError("Нет аккаунтов, вход невозможен.")

    login_name = input("Логин: ").strip()
    if login_name not in users:
        print("Пользователь не найден.")
        create_now = input(f"Создать аккаунт '{login_name}'? (y/n): ").strip().lower()
        if create_now == 'y':
            login_name = create_account()
            user_session(login_name, load_users())
            return
        else:
            raise UserNotFoundError(f"Пользователь '{login_name}' не найден.")

    for tries in range(3):
        master = getpass.getpass("Мастер-пароль: ")
        if master == users[login_name]["master_password"]:
            print("Вход выполнен!")
            user_session(login_name, users)
            return
        else:
            remaining = 2 - tries
            if remaining > 0:
                word = "попытки" if remaining == 2 else "попытка"
                print(f"Неверный пароль. У вас осталось {remaining} {word}!")
    raise AuthenticationError("Превышено количество попыток входа.")

def select_category(login_name: str, users: dict) -> str:
    """
    Позволяет пользователю выбрать категорию из списка доступных.

    Выводит стандартные и пользовательские категории, а также предлагает
    создать новую, если нужно.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    :type users: dict
    :returns: Название выбранной категории
    :rtype: str
    """
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
    """
    Выводит пароли пользователя, отфильтрованные по выбранной категории.

    Позволяет выбрать категорию (стандартную или пользовательскую) и
    показывает все пароли, относящиеся к ней.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    :type users: dict
    """
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
    """
    Выполняет поиск паролей по подстроке в названии ресурса.

    Поиск нечувствителен к регистру. Отображает совпадения с указанием
    категории и расшифрованным паролем.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    :type users: dict
    """
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

def get_categories():
    """
    Возвращает список стандартных категорий для группировки паролей.

    Эти категории используются при добавлении или просмотрах сохранённых
    паролей и не могут быть удалены или изменены пользователем.

    :returns: Список строк с названиями стандартных категорий
    :rtype: list[str]
    """
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
    """
    Выводит главное меню приложения на консоль.

    Отображает приветствие и три основные опции:
    создание аккаунта, вход в существующий аккаунт и выход из программы.
    Используется в главном цикле программы для навигации пользователя.
    """
    print("\n" + "="*40)
    print("Добро пожаловать в менеджер паролей MyKeyChain!")
    print("="*40)
    print("1. Создать аккаунт")
    print("2. Войти")
    print("3. Выход")
    print("="*40)

def user_menu():
    """
    Выводит меню действий для авторизованного пользователя.

    Содержит 8 опций: управление паролями (добавление, изменение, удаление),
    генерация, просмотр всех паролей, фильтрация по категории, поиск
    и выход из аккаунта. Вызывается в сессии пользователя.
    """
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
    """
    Главная точка входа в приложение MyKeyChain.

    Запускает бесконечный цикл главного меню, обрабатывает выбор пользователя
    и управляет потоком программы: создание аккаунта, вход или завершение работы.
    Все исключения перехватываются и отображаются в понятном виде.
    """
    while True:
        main_menu()
        choice = input("Выберите действие: ").strip()
        try:
            if choice == "1":
                login_name = create_account()
                user_session(login_name, load_users())
            elif choice == "2":
                login()
            elif choice == "3":
                print("Выход.")
                break
            else:
                print("Неверный выбор.")
        except MyKeyChainError as e:
            print(f"\n Ошибка: {e}")
        except KeyboardInterrupt:
            print("\nВыход по запросу пользователя.")
            break
        except Exception as e:
            print(f"\n❗ Критическая ошибка: {e}")

def user_session(login_name: str, users: dict):
    """
    Запускает интерактивную сессию для авторизованного пользователя.

    Обеспечивает циклическое отображение пользовательского меню и выполнение
    выбранных действий до тех пор, пока пользователь не выберет выход.
    Все операции (добавление, удаление, поиск и т.д.) выполняются в контексте
    текущего аккаунта. Перед выходом данные сохраняются на диск.

    :param login_name: Логин активного пользователя
    :type login_name: str
    :param users: Словарь всех пользовательских данных (для возможного изменения)
    :type users: dict
    """
    while True:
        user_menu()
        choice = input("Выбор: ").strip()
        try:
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
        except MyKeyChainError as e:
            print(f"\n Ошибка: {e}")
        except Exception as e:
            print(f"\n❗ Непредвиденная ошибка: {e}")

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
    """
    Создаёт новую пользовательскую категорию.

    Проверяет, что категория не дублирует существующие (включая стандартные),
    и сохраняет её в данных пользователя.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    :type users: dict
    :returns: Название созданной категории
    :rtype: str
    """
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
    Добавляет новый пароль для ресурса.

    :param login_name: Логин пользователя
    :type login_name: str
    :param users: Словарь пользователей
    :type users: dict
    :raises InvalidInputError: Если ресурс пустой
    :raises ResourceExistsError: Если ресурс уже существует
    """
    resource = input("Название ресурса: ").strip()
    if not resource:
        raise InvalidInputError("Название ресурса не может быть пустым.")
    if resource in users[login_name]["passwords"]:
        raise ResourceExistsError(f"Пароль для ресурса '{resource}' уже существует.")

    category = select_category(login_name, users)
    password = input("Пароль (оставьте пустым для генерации): ")
    if not password:
        password = generate_and_show_password(auto=True)

    shift = len(password)
    encrypted = caesar_cipher(password, shift)
    users[login_name]["passwords"][resource] = {"encrypted": encrypted, "category": category}
    print("Пароль добавлен.")

def update_password(login_name: str, users: dict):
    """
    Обновляет пароль для существующего ресурса.

    :raises InvalidInputError: Если ресурс пустой
    :raises ResourceNotFoundError: Если ресурс не найден
    """
    resource = input("Название ресурса: ").strip()
    if not resource:
        raise InvalidInputError("Название ресурса не может быть пустым.")
    if resource not in users[login_name]["passwords"]:
        raise ResourceNotFoundError(f"Ресурс '{resource}' не найден.")

    password = input("Новый пароль (оставьте пустым для генерации): ")
    if not password:
        password = generate_and_show_password(auto=True)

    shift = len(password)
    encrypted = caesar_cipher(password, shift)
    old_category = users[login_name]["passwords"][resource]["category"]
    users[login_name]["passwords"][resource] = {"encrypted": encrypted, "category": old_category}
    print("Пароль обновлён.")

def delete_password(login_name: str, users: dict):
    """
    Удаляет пароль для ресурса.

    :raises InvalidInputError: Если ресурс пустой
    :raises ResourceNotFoundError: Если ресурс не найден
    """
    resource = input("Название ресурса: ").strip()
    if not resource:
        raise InvalidInputError("Название ресурса не может быть пустым.")
    if resource not in users[login_name]["passwords"]:
        raise ResourceNotFoundError(f"Ресурс '{resource}' не найден.")

    confirm = input(f"Удалить пароль для '{resource}'? (y/n): ").strip().lower()
    if confirm == "y":
        del users[login_name]["passwords"][resource]
        print("Пароль удалён.")
    else:
        print("Удаление отменено.")

def generate_and_show_password(auto=False):
    """
    Взаимодействует с пользователем для генерации пароля по заданным параметрам.

    Запрашивает длину, использование цифр и специальных символов.
    Если auto=True, пароль возвращается без вывода на экран.

    :param auto: Флаг автоматического режима (без вывода результата)
    :type auto: bool
    :returns: Сгенерированный пароль
    :rtype: str
    """
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
    """
    Выводит все сохранённые пароли пользователя, сгруппированные по категориям.

    Пароли расшифровываются на лету с использованием шифра Цезаря и
    отображаются в читаемом виде только на экране.

    :param login_name: Логин текущего пользователя
    :type login_name: str
    :param users: Словарь пользователей и их данных
    :type users: dict
    """
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
    main()