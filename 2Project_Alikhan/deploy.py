#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 6):
        print("Ошибка: Требуется Python 3.6 или выше.")
        sys.exit(1)
    print("✅ Проверка версии Python пройдена.")

def install_requirements():
    """Установка необходимых пакетов"""
    print("Установка необходимых пакетов...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Требования успешно установлены.")
    except subprocess.CalledProcessError:
        print("Ошибка: Не удалось установить требования.")
        sys.exit(1)

def create_directories():
    """Создание необходимых директорий"""
    print("Создание необходимых директорий...")
    os.makedirs("vacancies", exist_ok=True)
    print("✅ Директории созданы.")

def check_bot_token():
    """Проверка токена бота"""
    from telegram_bot import BOT_TOKEN
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Предупреждение: Токен бота может быть установлен неправильно.")
        print("Пожалуйста, проверьте переменную BOT_TOKEN в telegram_bot.py")
    else:
        print("✅ Токен бота установлен.")

def run_application():
    """Запуск приложения"""
    print("\nЗапуск приложения...")
    try:
        if platform.system() == "Windows":
            os.system("start cmd /k python main.py")
        else:
            os.system("python main.py &")
        print("✅ Приложение запущено.")
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        sys.exit(1)

def main():
    """Основная функция деплоя"""
    print("=" * 50)
    print("Деплой HH.ru Python Vacancy Bot")
    print("=" * 50)
    
    # Проверка версии Python
    check_python_version()
    
    # Установка требований
    install_requirements()
    
    # Создание директорий
    create_directories()
    
    # Проверка токена бота
    check_bot_token()
    
    # Спрашиваем пользователя, хочет ли он запустить приложение
    print("\nДеплой успешно завершен!")
    run_app = input("Хотите запустить приложение сейчас? (y/n): ").lower()
    
    if run_app == 'y':
        run_application()
    else:
        print("\nЧтобы запустить приложение позже, используйте команду:")
        print("python main.py")
    
    print("\nСпасибо за использование HH.ru Python Vacancy Bot!")

if __name__ == "__main__":
    main() 