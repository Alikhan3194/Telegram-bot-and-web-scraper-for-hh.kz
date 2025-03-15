import os
import logging
import threading
import time
import argparse
from datetime import datetime

from web_hh_scrapping import HHScraper
from db_manager import DatabaseManager
import telegram_bot

# Configure logging
logging.basicConfig(
    filename='main.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_directories():
    """Setup necessary directories for the project"""
    dirs = ['data', 'logs']
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            logging.info(f"Created directory: {dir_name}")

def run_scraper(search_query, pages, interval):
    """Run the scraper in a separate thread"""
    logging.info(f"Starting scraper for query '{search_query}' on {pages} pages with {interval}s interval")
    
    scraper = HHScraper(
        search_query=search_query,
        pages_to_scrape=pages,
        update_interval=interval
    )
    
    # Run the initial update
    db = DatabaseManager()
    all_vacancies, new_vacancies, updated_vacancies, all_file, new_file = scraper.run_once()
    
    if new_vacancies:
        added_count = db.add_multiple_vacancies(new_vacancies)
        logging.info(f"Added {added_count} new vacancies to the database")
    
    # Continue running scraper in a loop
    scraper_thread = threading.Thread(target=scraper.run)
    scraper_thread.daemon = True
    scraper_thread.start()
    
    return scraper_thread

def run_bot():
    """Run the Telegram bot"""
    logging.info("Starting Telegram bot")
    bot_thread = threading.Thread(target=telegram_bot.asyncio.run, args=(telegram_bot.main(),))
    bot_thread.daemon = True
    bot_thread.start()
    return bot_thread

def main():
    """Main function to run the application"""
    parser = argparse.ArgumentParser(description='HH.kz Python job vacancy scraper and Telegram bot')
    
    parser.add_argument('--search', type=str, default='Python', help='Search query for vacancies')
    parser.add_argument('--pages', type=int, default=3, help='Number of pages to scrape')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scraping runs in seconds')
    parser.add_argument('--scraper-only', action='store_true', help='Run only the scraper without the bot')
    parser.add_argument('--bot-only', action='store_true', help='Run only the bot without the scraper')
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Initialize the database
    db = DatabaseManager()
    db.create_tables()
    
    try:
        # Start components based on arguments
        if args.bot_only:
            logging.info("Running in bot-only mode")
            bot_thread = run_bot()
            bot_thread.join()
        elif args.scraper_only:
            logging.info("Running in scraper-only mode")
            scraper_thread = run_scraper(args.search, args.pages, args.interval)
            scraper_thread.join()
        else:
            logging.info("Running both scraper and bot")
            scraper_thread = run_scraper(args.search, args.pages, args.interval)
            bot_thread = run_bot()
            
            # Keep the main thread alive
            while True:
                time.sleep(60)
                logging.info(f"System running. Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
    except KeyboardInterrupt:
        logging.info("Application stopped by user")
    except Exception as e:
        logging.error(f"Error in main application: {e}")
        
if __name__ == "__main__":
    main() 
