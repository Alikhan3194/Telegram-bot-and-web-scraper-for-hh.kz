#!/usr/bin/env python
"""
Deployment script for HH.kz Python Job Vacancy Scraper and Telegram Bot
This script helps users set up and deploy the application in various environments.
"""

import os
import sys
import subprocess
import logging
import argparse
import platform
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_python_version():
    """Check if Python version is compatible (3.6+)"""
    required_version = (3, 6)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        logging.error(f"Python {required_version[0]}.{required_version[1]} or higher is required. "
                     f"You're using Python {current_version[0]}.{current_version[1]}.")
        return False
    return True

def setup_virtual_env(env_name="venv"):
    """Set up a virtual environment"""
    if os.path.exists(env_name):
        logging.info(f"Virtual environment '{env_name}' already exists")
        return True
    
    try:
        logging.info(f"Creating virtual environment '{env_name}'...")
        subprocess.run([sys.executable, "-m", "venv", env_name], check=True)
        logging.info("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create virtual environment: {e}")
        return False

def install_requirements(env_name="venv"):
    """Install requirements in the virtual environment"""
    if not os.path.exists("requirements.txt"):
        logging.error("requirements.txt not found")
        return False
    
    try:
        # Determine the pip path based on the platform
        if platform.system() == "Windows":
            pip_path = os.path.join(env_name, "Scripts", "pip")
        else:
            pip_path = os.path.join(env_name, "bin", "pip")
        
        logging.info("Installing requirements...")
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        logging.info("Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install requirements: {e}")
        return False

def setup_database():
    """Set up the database"""
    try:
        # Determine the python path based on the platform
        if platform.system() == "Windows":
            python_path = os.path.join("venv", "Scripts", "python")
        else:
            python_path = os.path.join("venv", "bin", "python")
        
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        
        # Import database manager and create tables
        logging.info("Setting up database...")
        script = (
            "from db_manager import DatabaseManager; "
            "db = DatabaseManager(); "
            "db.create_tables(); "
            "print('Database setup complete')"
        )
        subprocess.run([python_path, "-c", script], check=True)
        logging.info("Database setup successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to set up database: {e}")
        return False

def configure_bot_token(token=None):
    """Configure the Telegram bot token"""
    if not token:
        token = input("Enter your Telegram bot token (from BotFather): ").strip()
    
    if not token:
        logging.warning("No token provided. You'll need to update the token manually in telegram_bot.py")
        return False
    
    try:
        with open("telegram_bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace the BOT_TOKEN in the file
        if "BOT_TOKEN = " in content:
            content = content.replace('BOT_TOKEN = "8181311299:AAH7RECw8gnwE7vlgR-sZNMzeGjSkPdt2vM"', f'BOT_TOKEN = "{token}"')
            
            with open("telegram_bot.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            logging.info("Bot token configured successfully")
            return True
        else:
            logging.warning("Could not find BOT_TOKEN in telegram_bot.py. You'll need to update it manually.")
            return False
    except Exception as e:
        logging.error(f"Failed to configure bot token: {e}")
        return False

def create_startup_script():
    """Create a startup script for the application"""
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Create a batch file for Windows
        script_content = """@echo off
echo Starting HH.kz Python Job Vacancy Scraper and Telegram Bot...
call venv\\Scripts\\activate
python main.py
pause
"""
        script_name = "start_app.bat"
    else:
        # Create a shell script for Unix-like systems
        script_content = """#!/bin/bash
echo "Starting HH.kz Python Job Vacancy Scraper and Telegram Bot..."
source venv/bin/activate
python main.py
"""
        script_name = "start_app.sh"
    
    try:
        with open(script_name, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # Make the script executable on Unix-like systems
        if not is_windows:
            os.chmod(script_name, 0o755)
        
        logging.info(f"Created startup script: {script_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to create startup script: {e}")
        return False

def generate_systemd_service():
    """Generate a systemd service file for Linux deployment"""
    if platform.system() != "Linux":
        logging.info("Systemd service generation is only available on Linux")
        return False
    
    try:
        # Get the absolute path to the project directory
        project_dir = os.path.abspath(".")
        
        # Generate the service file content
        service_content = f"""[Unit]
Description=HH.kz Python Job Vacancy Scraper and Telegram Bot
After=network.target

[Service]
Type=simple
User={os.getlogin()}
WorkingDirectory={project_dir}
ExecStart={project_dir}/venv/bin/python {project_dir}/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        # Write the service file
        service_file = "hh_bot.service"
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(service_content)
        
        logging.info(f"Generated systemd service file: {service_file}")
        logging.info(f"To install the service, run:")
        logging.info(f"  sudo cp {service_file} /etc/systemd/system/")
        logging.info(f"  sudo systemctl daemon-reload")
        logging.info(f"  sudo systemctl enable {service_file}")
        logging.info(f"  sudo systemctl start {service_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to generate systemd service: {e}")
        return False

def check_and_create_directories():
    """Check and create necessary directories"""
    try:
        # Create directories if they don't exist
        dirs = ["data", "logs"]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created directory: {directory}")
        return True
    except Exception as e:
        logging.error(f"Failed to create directories: {e}")
        return False

def main():
    """Main function for the deployment script"""
    parser = argparse.ArgumentParser(description="Deploy HH.kz Python Job Vacancy Scraper and Telegram Bot")
    
    parser.add_argument("--venv", type=str, default="venv", help="Name of the virtual environment")
    parser.add_argument("--token", type=str, help="Telegram bot token from BotFather")
    parser.add_argument("--systemd", action="store_true", help="Generate systemd service file (Linux only)")
    parser.add_argument("--no-setup", action="store_true", help="Skip environment setup and just create startup scripts")
    
    args = parser.parse_args()
    
    logging.info("Starting deployment...")
    
    if not args.no_setup:
        # Check Python version
        if not check_python_version():
            return
        
        # Setup virtual environment
        if not setup_virtual_env(args.venv):
            return
        
        # Install requirements
        if not install_requirements(args.venv):
            return
        
        # Create necessary directories
        if not check_and_create_directories():
            return
        
        # Setup database
        if not setup_database():
            logging.warning("Database setup encountered issues, but continuing...")
        
        # Configure bot token
        if args.token:
            configure_bot_token(args.token)
        else:
            logging.info("No token provided. You can configure it later.")
    
    # Create startup script
    create_startup_script()
    
    # Generate systemd service file if requested and on Linux
    if args.systemd:
        generate_systemd_service()
    
    logging.info("Deployment complete!")
    logging.info("You can start the application using the startup script.")

if __name__ == "__main__":
    main() 
