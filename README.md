# HH.kz Python Job Vacancy Scraper and Telegram Bot

This project provides a system for scraping Python job vacancies from hh.kz and making them accessible through a Telegram bot. The application consists of a web scraper, database manager, and Telegram bot, all working together to deliver real-time job vacancy notifications and search capabilities.

## Features

- 🔍 **Web Scraper**: Scrapes Python job vacancies from hh.kz, extracting detailed information including:
  - Job title and company
  - Salary information
  - Required experience
  - Location
  - Required skills
  - Publication date
  
- 💾 **Database Management**:
  - Stores all vacancies in a SQLite database
  - Tracks new and updated vacancies
  - Manages user subscriptions for notifications
  - Records which notifications have been sent to users
  
- 🤖 **Telegram Bot**:
  - `/start` - Introduction to the bot and available commands
  - `/help` - Detailed help on using the bot
  - `/find [query]` - Search for vacancies containing specific terms
  - `/search [keyword]` - Search for vacancies with specific keywords in title or skills
  - `/latest` - Show the latest 5 vacancies
  - `/update` - Manually trigger a vacancy database update
  - `/subscribe` - Subscribe to receive notifications about new vacancies
  - `/unsubscribe` - Stop receiving notifications
  - `/stats` - Show detailed database statistics

- 📊 **Statistics and Analysis**:
  - Track most common companies hiring Python developers
  - Track most demanded skills in Python job listings
  - Monitor total vacancy counts and trends

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hh-python-scraper.git
   cd hh-python-scraper
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Telegram bot:
   - Create a new bot using BotFather on Telegram
   - Get your bot token
   - Update the `BOT_TOKEN` variable in `telegram_bot.py`

## Usage

### Running the complete system

To run both the scraper and Telegram bot:

```bash
python main.py
```

### Command-line options

The application supports various command-line options:

```bash
python main.py --help
```

Options:
- `--search TEXT` - Specify the search query (default: "Python")
- `--pages NUMBER` - Number of pages to scrape (default: 3)
- `--interval SECONDS` - Interval between scraping runs in seconds (default: 600)
- `--scraper-only` - Run only the scraper without the bot
- `--bot-only` - Run only the bot without the scraper

Examples:
```bash
# Run with custom search query
python main.py --search "Python Django"

# Run only the Telegram bot
python main.py --bot-only

# Run only the scraper with custom settings
python main.py --scraper-only --pages 5 --interval 1800
```

## Project Structure

- `main.py` - Main entry point to run the complete system
- `web_hh_scrapping.py` - Web scraper for hh.kz
- `db_manager.py` - Database operations and management
- `telegram_bot.py` - Telegram bot implementation with commands
- `requirements.txt` - Required Python packages
- `data/` - Directory for storing JSON files and database
- `logs/` - Directory for log files

## Telegram Bot Commands

The Telegram bot supports the following commands:

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and get an introduction |
| `/help` | Display detailed help on using the bot |
| `/find [query]` | Search for vacancies containing the specified query |
| `/search [keyword]` | Search for vacancies with a specific keyword in title or skills |
| `/latest` | Show the 5 most recently added vacancies |
| `/update` | Manually trigger an update to fetch new vacancies |
| `/subscribe` | Subscribe to receive notifications about new vacancies |
| `/unsubscribe` | Unsubscribe from vacancy notifications |
| `/stats` | Show detailed statistics about the vacancy database |

## Contributions

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
