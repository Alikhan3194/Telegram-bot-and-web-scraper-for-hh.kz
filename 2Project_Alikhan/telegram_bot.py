import logging
import asyncio
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.markdown import hbold, hlink, hitalic, hcode
from datetime import datetime
import threading
import time
import schedule
import os
import json

from web_hh_scrapping import HHScraper
from db_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    
    # Add salary information
    salary_text = ""
    if vacancy.get('salary') and vacancy.get('salary') != "Not specified":
        salary_text = f"\n{hbold('Salary:')} {vacancy['salary']}"
    
    # Add experience information
    exp_text = ""
    if vacancy.get('experience') and vacancy.get('experience') != "Not specified":
        exp_text = f"\n{hbold('Experience:')} {vacancy['experience']}"
    
    # Add location information
    location_text = ""
    if vacancy.get('location') and vacancy.get('location') != "Not specified":
        location_text = f"\n{hbold('Location:')} {vacancy['location']}"
    
    return (
        f"{hbold('Vacancy:')} {vacancy['title']}\n"
        f"{hbold('Company:')} {vacancy['company']}"
        f"{salary_text}"
        f"{exp_text}"
        f"{location_text}"
        f"{skills_text}\n"
        f"{hbold('Link:')} {hlink('Open vacancy', vacancy['link'])}\n"
        f"{hitalic('Added:')} {vacancy['created_at']}\n"
    )

# Command handler for /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        f"Hello, {message.from_user.first_name}!\n\n"
        f"I'm a bot that helps you find Python vacancies on hh.kz.\n\n"
        f"Available commands:\n"
        f"/find [query] - Search for vacancies with a specific query\n"
        f"/search [keyword] - Search for vacancies with a specific keyword\n"
        f"/latest - Show the latest 5 vacancies\n"
        f"/update - Manually update the vacancy database\n"
        f"/subscribe - Subscribe to new vacancy notifications\n"
        f"/unsubscribe - Unsubscribe from notifications\n"
        f"/stats - Show detailed database statistics\n"
        f"/help - Display this help message"
    )

# Command handler for /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    logging.info(f"User {message.from_user.id} requested help")
    await message.answer(
        f"{hbold('Available Commands:')}\n\n"
        f"{hbold('/find [query]')} - Search for vacancies containing the specified query\n"
        f"Example: {hcode('/find Python Django')}\n\n"
        f"{hbold('/search [keyword]')} - Search for vacancies with a specific keyword in title or skills\n"
        f"Example: {hcode('/search Django')}\n\n"
        f"{hbold('/latest')} - Show the 5 most recently added vacancies\n\n"
        f"{hbold('/update')} - Manually trigger an update to fetch new vacancies\n\n"
        f"{hbold('/subscribe')} - Subscribe to receive notifications about new vacancies\n\n"
        f"{hbold('/unsubscribe')} - Unsubscribe from vacancy notifications\n\n"
        f"{hbold('/stats')} - Show detailed statistics about the vacancy database\n\n"
        f"{hbold('/help')} - Display this help message"
    )

# Command handler for /find
@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    # Extract the search query from the message
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        await message.answer("Please provide a search term. Example: /find Python Django")
        return
    
    search_term = command_parts[1]
    logging.info(f"User {message.from_user.id} searching for '{search_term}'")
    await message.answer(f"Searching for vacancies with '{search_term}'...")
    
    # Search for vacancies in the database
    vacancies = db.get_vacancies_by_keyword(search_term, limit=10)
    
    if not vacancies:
        await message.answer(f"No vacancies found for '{search_term}'.")
        return
    
    # Send the results
    await message.answer(f"Found {len(vacancies)} vacancies for '{search_term}':")
    
    for vacancy in vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /search (similar to find but this explicitly mentions it searches skills too)
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    # Extract the search query from the message
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        await message.answer("Please provide a keyword to search in titles and skills. Example: /search Django")
        return
    
    search_term = command_parts[1]
    logging.info(f"User {message.from_user.id} searching for keyword '{search_term}'")
    await message.answer(f"Searching for vacancies with keyword '{search_term}' in title or skills...")
    
    # Search for vacancies in the database
    vacancies = db.get_vacancies_by_keyword(search_term, limit=10)
    
    if not vacancies:
        await message.answer(f"No vacancies found with keyword '{search_term}'.")
        return
    
    # Send the results
    await message.answer(f"Found {len(vacancies)} vacancies with keyword '{search_term}':")
    
    for vacancy in vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /latest
@dp.message(Command("latest"))
async def cmd_latest(message: types.Message):
    logging.info(f"User {message.from_user.id} requested latest vacancies")
    await message.answer("Getting the latest vacancies...")
    
    # Get the latest vacancies from the database
    latest_vacancies = db.get_latest_vacancies(limit=5)
    
    if not latest_vacancies:
        await message.answer("No vacancies found in the database.")
        return
    
    # Send the results
    await message.answer(f"Latest {len(latest_vacancies)} vacancies:")
    
    for vacancy in latest_vacancies:
        await message.answer(format_vacancy(vacancy), parse_mode="HTML", disable_web_page_preview=False)

# Command handler for /update
@dp.message(Command("update"))
async def cmd_update(message: types.Message):
    global is_updating
    
    if is_updating:
        await message.answer("Update is already in progress. Please wait...")
        return
    
    logging.info(f"User {message.from_user.id} triggered manual update")
    await message.answer("Starting manual update of vacancies...")
    
    # Run the update in a separate thread to avoid blocking the bot
    update_thread = threading.Thread(target=update_vacancies, args=(message.chat.id,))
    update_thread.start()

# Command handler for /subscribe
@dp.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"User {user_id} subscribing to vacancy updates")
    
    # Add user to subscribers
    if db.add_subscription(user_id):
        await message.answer(
            "You have successfully subscribed to Python vacancy updates!\n\n"
            "You will receive notifications when new vacancies are found.\n\n"
            "To unsubscribe, use the /unsubscribe command."
        )
    else:
        await message.answer("Failed to subscribe. Please try again later.")

# Command handler for /unsubscribe
@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"User {user_id} unsubscribing from vacancy updates")
    
    # Remove user from subscribers
    if db.remove_subscription(user_id):
        await message.answer(
            "You have been unsubscribed from vacancy updates.\n\n"
            "You will no longer receive notifications about new vacancies.\n\n"
            "To subscribe again, use the /subscribe command."
        )
    else:
        await message.answer("Failed to unsubscribe. Please try again later.")

# Command handler for /stats
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    logging.info(f"User {message.from_user.id} requested statistics")
    await message.answer("Gathering database statistics...")
    
    # Get detailed statistics
    stats = db.get_stats()
    
    if 'error' in stats:
        await message.answer(f"Error retrieving statistics: {stats['error']}")
        return
    
    # Format top companies
    companies_text = ""
    if 'companies' in stats and stats['companies']:
        companies_text = "\n\nTop Companies:\n"
        for i, company in enumerate(stats['companies'], 1):
            companies_text += f"{i}. {company['name']} - {company['count']} vacancies\n"
    
    # Format top skills
    skills_text = ""
    if 'skills' in stats and stats['skills']:
        skills_text = "\n\nTop Skills in Demand:\n"
        for i, skill in enumerate(stats['skills'], 1):
            skills_text += f"{i}. {skill['name']} - {skill['count']} occurrences\n"
    
    # Send statistics
    await message.answer(
        f"Database Statistics\n\n"
        f"Total Python vacancies: {stats.get('total_vacancies', 0)}\n"
        f"Active subscribers: {stats.get('active_subscribers', 0)}"
        f"{companies_text}"
        f"{skills_text}\n\n"
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# Function to update vacancies and notify the chat
def update_vacancies(chat_id=None):
    global is_updating
    
    try:
        is_updating = True
        logging.info("Starting vacancy update")
        
        # Run the scraper once
        _, new_vacancies, _, all_vacancies_file, new_vacancies_file = scraper.run_once()
        
        # Add new vacancies to the database
        added_count = db.add_multiple_vacancies(new_vacancies)
        
        # Notify the chat if a chat_id is provided
        if chat_id and added_count > 0:
            asyncio.run(bot.send_message(
                chat_id,
                f" Update completed!\n\n"
                f"Added {added_count} new Python vacancies to the database.\n"
                f"All vacancies saved to: {os.path.basename(all_vacancies_file)}\n"
                f"New vacancies saved to: {os.path.basename(new_vacancies_file) if new_vacancies_file else 'None'}"
            ))
        elif chat_id:
            asyncio.run(bot.send_message(
                chat_id,
                " Update completed! No new vacancies found."
            ))
        
        # Notify subscribers about new vacancies
        if added_count > 0:
            notify_subscribers(new_vacancies)
            
        logging.info(f"Update completed. Added {added_count} new vacancies.")
        
    except Exception as e:
        logging.error(f"Error during update: {e}")
        if chat_id:
            asyncio.run(bot.send_message(
                chat_id,
                f"Error during update: {str(e)}"
            ))
    finally:
        is_updating = False

# Function to notify subscribers about new vacancies
def notify_subscribers(new_vacancies):
    if not new_vacancies:
        return
    
    subscribers = db.get_all_active_subscribers()
    logging.info(f"Notifying {len(subscribers)} subscribers about {len(new_vacancies)} new vacancies")
    
    for subscriber in subscribers:
        user_id = subscriber['user_id']
        
        try:
            # Send notification about new vacancies
            asyncio.run(bot.send_message(
                user_id,
                f"Found {len(new_vacancies)} new Python vacancies!\n\n"
                f"Here are some of the latest openings:"
            ))
            
            # Send up to 3 newest vacancies
            for i, vacancy in enumerate(new_vacancies[:3]):
                asyncio.run(bot.send_message(
                    user_id,
                    format_vacancy(vacancy),
                    parse_mode="HTML",
                    disable_web_page_preview=False
                ))
                
                # Record that we sent this notification
                db.add_notification(user_id, vacancy['id'])
                
            # If there are more than 3 vacancies, suggest using /latest
            if len(new_vacancies) > 3:
                asyncio.run(bot.send_message(
                    user_id,
                    f"There are {len(new_vacancies) - 3} more new vacancies. "
                    f"Use /latest to see the most recent ones, or /search to find specific vacancies."
                ))
                
            logging.info(f"Sent vacancy notifications to user {user_id}")
                
        except Exception as e:
            logging.error(f"Error sending notifications to user {user_id}: {e}")

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
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Run the initial update to populate the database
    logging.info("Running initial update to populate the database...")
    update_vacancies()
    
    # Start the bot
    logging.info("Starting the bot...")
    asyncio.run(main()) 
