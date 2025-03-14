# HH.ru Python Vacancy Scraper and Telegram Bot

This project consists of a web scraper for hh.ru (HeadHunter) that collects Python job vacancies and a Telegram bot that allows users to search and receive updates about these vacancies.

## Features

### Web Scraper
- Scrapes Python job vacancies from hh.ru
- Extracts vacancy title, company name, link, and skills
- Saves all vacancies to JSON files with timestamps
- Identifies and separately saves new and existing vacancies
- Automatically updates at specified intervals (default: 10 minutes)
- Handles pagination to collect all available vacancies

### SQLite Database
- Stores all vacancy information in a SQLite database
- Provides CRUD operations for vacancy data
- Enables efficient searching and retrieval of vacancies

### Telegram Bot
- Allows users to search for vacancies using the `/find` command
- Shows the latest 5 vacancies with the `/latest` command
- Manually updates the vacancy database with the `/update` command
- Displays database statistics with the `/stats` command
- Automatically updates the database every 10 minutes
- Notifies users about new vacancies

## Requirements

- Python 3.6+
- Required packages (see requirements.txt):
  - requests
  - beautifulsoup4
  - lxml
  - aiogram
  - schedule
  - asyncio
  - python-dotenv

## Installation

1. Make sure you have Python 3.6 or higher installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Full Application

To run both the scraper and Telegram bot:

```bash
python main.py
```

This will:
1. Start the Telegram bot
2. Run an initial scraping to populate the database
3. Schedule automatic updates every 10 minutes

### Telegram Bot Commands

- `/start` - Get information about the bot and available commands
- `/find Python` - Search for Python vacancies (you can add more keywords, e.g., `/find Python Django`)
- `/latest` - Show the 5 most recently added vacancies
- `/update` - Manually trigger a database update
- `/stats` - Show database statistics

## Project Structure

- `web_hh_scrapping.py` - The web scraper for hh.ru
- `db_manager.py` - SQLite database manager
- `telegram_bot.py` - Telegram bot implementation
- `main.py` - Main entry point for the application
- `requirements.txt` - List of required packages
- `vacancies/` - Directory for JSON files with scraped vacancies
- `vacancies.db` - SQLite database file

## Customization

You can modify the project to:

- Change the search query (default: "Python")
- Change the region (default: "160" for Almaty)
- Adjust the update interval (default: 600 seconds)
- Modify the maximum number of pages to scrape (default: 20)
- Change the Telegram bot token

## Notes

- The scraper uses a delay between page requests to avoid overloading the server
- The bot runs updates in a separate thread to avoid blocking the main thread
- The database is automatically created if it doesn't exist
- All errors are logged to the console and a log file 
