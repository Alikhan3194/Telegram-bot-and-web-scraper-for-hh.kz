import logging
import asyncio
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.markdown import hbold, hlink
from datetime import datetime
import threading
import time
import schedule

from web_hh_scrapping import HHScraper
from db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize bot with token
BOT_TOKEN = "8181311299:AAH7RECw8gnwE7vlgR-sZNMzeGjSkPdt2vM"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Initialize database manager
db = DatabaseManager()

# Initialize scraper
scraper = HHScraper(search_query="Python")

# Global variable to track if update is running
is_updating = False

# Function to format vacancy for display in Telegram
def format_vacancy(vacancy):
    skills_text = ""
    if vacancy.get('skills'):
        skills_list = vacancy.get('skills', [])
        if skills_list:
            skills_text = f"\n{hbold('Skills:')} {', '.join(skills_list)}"
    
    return (
        f"{hbold('Vacancy:')} {vacancy['title']}\n"
        f"{hbold('Company:')} {vacancy['company']}\n"
        f"{hbold('Link:')} {hlink('Open vacancy', vacancy['link'])}"
        f"{skills_text}\n"
        f"{hbold('Added:')} {vacancy['created_at']}\n"
    )

# Command handler for /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я бот, который помогает найти вакансии Python на hh.ru.\n\n"
        f"Доступные команды:\n"
        f"/find Python - Поиск вакансий Python\n"
        f"/search Django - Поиск вакансий по ключевому слову\n"
        f"/latest - Показать последние 5 вакансий\n"
        f"/update - Обновить базу данных вакансий вручную\n"
        f"/subscribe - Подписаться на обновления новых вакансий\n"
        f"/unsubscribe - Отписаться от обновлений\n"
        f"/stats - Показать статистику базы данных"
    )

# Command handler for /find
@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} ищет вакансии Python")
    await message.answer("🔍 Ищу вакансии Python...")
    
    # Search for vacancies in the database
    vacancies = db.search_vacancies("Python", limit=10)
    
    if not vacancies:
        await message.answer("Вакансии Python не найдены.")
        return
    
    # Send the results
    await message.answer(f"Найдено {len(vacancies)} вакансий Python:")
    
    for vacancy in vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /search
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    # Extract the search query from the message
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        await message.answer("Пожалуйста, укажите поисковый запрос. Пример: /search Django")
        return
    
    search_term = command_parts[1]
    logging.info(f"Пользователь {message.from_user.id} ищет вакансии по запросу '{search_term}'")
    await message.answer(f"🔍 Ищу вакансии по запросу '{search_term}'...")
    
    # Search for vacancies in the database
    vacancies = db.search_vacancies(search_term, limit=10)
    
    if not vacancies:
        await message.answer(f"Вакансии по запросу '{search_term}' не найдены.")
        return
    
    # Send the results
    await message.answer(f"Найдено {len(vacancies)} вакансий по запросу '{search_term}':")
    
    for vacancy in vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /latest
@dp.message(Command("latest"))
async def cmd_latest(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} запросил последние вакансии")
    await message.answer("🕒 Получаю последние вакансии...")
    
    # Get the latest vacancies from the database
    latest_vacancies = db.get_latest_vacancies(limit=5)
    
    if not latest_vacancies:
        await message.answer("В базе данных нет вакансий.")
        return
    
    # Send the results
    await message.answer(f"Последние {len(latest_vacancies)} вакансий:")
    
    for vacancy in latest_vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /update
@dp.message(Command("update"))
async def cmd_update(message: types.Message):
    global is_updating
    
    if is_updating:
        await message.answer("⏳ Обновление уже выполняется. Пожалуйста, подождите...")
        return
    
    logging.info(f"Пользователь {message.from_user.id} запустил обновление вакансий")
    await message.answer("🔄 Начинаю обновление вакансий...")
    
    # Run the update in a separate thread to avoid blocking the bot
    update_thread = threading.Thread(target=update_vacancies, args=(message.chat.id,))
    update_thread.start()

# Command handler for /subscribe
@dp.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    user_id = message.from_user.id
    
    # Add user to subscribers
    if db.add_subscription(user_id):
        logging.info(f"Пользователь {user_id} подписался на обновления")
        await message.answer("✅ Вы успешно подписались на обновления новых вакансий!\n\nВы будете получать уведомления о новых вакансиях Python.")
    else:
        await message.answer("❌ Не удалось подписаться на обновления. Пожалуйста, попробуйте позже.")

# Command handler for /unsubscribe
@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message):
    user_id = message.from_user.id
    
    # Remove user from subscribers
    if db.remove_subscription(user_id):
        logging.info(f"Пользователь {user_id} отписался от обновлений")
        await message.answer("✅ Вы успешно отписались от обновлений.")
    else:
        await message.answer("❌ Не удалось отписаться от обновлений. Пожалуйста, попробуйте позже.")

# Command handler for /stats
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    total_vacancies = db.count_vacancies()
    logging.info(f"Пользователь {message.from_user.id} запросил статистику")
    await message.answer(f"📊 Статистика базы данных:\n\nВсего вакансий: {total_vacancies}")

# Function to update vacancies and notify the chat
def update_vacancies(chat_id=None):
    global is_updating
    
    try:
        is_updating = True
        logging.info("Начало обновления вакансий")
        
        # Run the scraper once
        _, new_vacancies, _ = scraper.run_once()
        
        # Add new vacancies to the database
        added_count = db.add_multiple_vacancies(new_vacancies)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scraper.save_to_json(new_vacancies, f"new_vacancies_{timestamp}.json")
        
        # Notify the chat if a chat_id is provided
        if chat_id and added_count > 0:
            asyncio.run(bot.send_message(
                chat_id,
                f"✅ Обновление завершено!\n\nДобавлено {added_count} новых вакансий в базу данных."
            ))
        elif chat_id:
            asyncio.run(bot.send_message(
                chat_id,
                "✅ Обновление завершено! Новых вакансий не найдено."
            ))
        
        # Notify subscribers about new vacancies
        if added_count > 0:
            notify_subscribers(new_vacancies)
            
        logging.info(f"Обновление завершено. Добавлено {added_count} новых вакансий.")
        
    except Exception as e:
        logging.error(f"Ошибка при обновлении: {e}")
        if chat_id:
            asyncio.run(bot.send_message(
                chat_id,
                f"❌ Ошибка при обновлении: {str(e)}"
            ))
    finally:
        is_updating = False

# Function to notify subscribers about new vacancies
def notify_subscribers(new_vacancies):
    if not new_vacancies:
        return
    
    subscribers = db.get_all_subscribers()
    logging.info(f"Отправка уведомлений {len(subscribers)} подписчикам о {len(new_vacancies)} новых вакансиях")
    
    for subscriber in subscribers:
        user_id = subscriber['user_id']
        
        try:
            # Send notification about new vacancies
            asyncio.run(bot.send_message(
                user_id,
                f"🔔 Найдено {len(new_vacancies)} новых вакансий Python!"
            ))
            
            # Send up to 3 new vacancies
            for vacancy in new_vacancies[:3]:
                asyncio.run(bot.send_message(
                    user_id,
                    format_vacancy(vacancy),
                    parse_mode="HTML",
                    disable_web_page_preview=False
                ))
                
            # If there are more than 3 vacancies, suggest using /latest
            if len(new_vacancies) > 3:
                asyncio.run(bot.send_message(
                    user_id,
                    f"И еще {len(new_vacancies) - 3} вакансий. Используйте /latest, чтобы увидеть последние вакансии."
                ))
                
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

# Schedule regular updates
def schedule_updates():
    schedule.every(10).minutes.do(update_vacancies)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main function to start the bot
async def main():
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_updates)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the bot
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Run the initial update to populate the database
    logging.info("Запуск начального обновления для заполнения базы данных...")
    update_vacancies()
    
    # Start the bot
    logging.info("Запуск бота...")
    asyncio.run(main()) 