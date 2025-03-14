import asyncio
import logging
import os
from telegram_bot import main as bot_main

# Настройка логирования
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Запуск HH.ru Python Vacancy Bot")
    
    # Создаем необходимые директории
    os.makedirs("vacancies", exist_ok=True)
    
    try:
        # Запускаем бота
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в main: {e}", exc_info=True) 