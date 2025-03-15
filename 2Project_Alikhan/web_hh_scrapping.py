import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from datetime import datetime
import re
from typing import List, Dict, Tuple, Any, Optional

# Setup logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HHScraper:
    def __init__(self, search_query: str, pages_to_scrape: int = 3, update_interval: int = 600):
        """
        Initialize the scraper with the search query and configuration.
        
        Args:
            search_query: The search term to look for vacancies
            pages_to_scrape: Number of pages to scrape (default: 3)
            update_interval: Time between updates in seconds (default: 600 = 10 minutes)
        """
        self.search_query = search_query
        self.pages_to_scrape = pages_to_scrape
        self.update_interval = update_interval
        self.base_url = "https://hh.kz/search/vacancy"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.all_vacancies_file = os.path.join(self.output_dir, "all_vacancies.json")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"Created output directory: {self.output_dir}")

    def fetch_html(self, url: str, params: Dict = None) -> str:
        """
        Fetch HTML content from the URL.
        
        Args:
            url: The URL to fetch
            params: Query parameters to include in the request
            
        Returns:
            HTML content as a string
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching HTML: {e}")
            return ""

    def parse_vacancies(self, html: str) -> List[Dict]:
        """
        Parse the HTML to extract vacancy information.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of vacancy dictionaries
        """
        vacancies = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all vacancy blocks
        vacancy_blocks = soup.find_all('div', {'class': 'vacancy-serp-item-body'})
        
        for block in vacancy_blocks:
            try:
                # Extract basic information
                title_element = block.find('a', {'class': 'serp-item__title'})
                if not title_element:
                    continue
                
                title = title_element.text.strip()
                link = title_element['href'].split('?')[0]  # Remove query parameters
                
                # Extract company name
                company_element = block.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
                company = company_element.text.strip() if company_element else "Company not specified"
                
                # Extract skills if available
                skills = []
                skills_block = block.find('div', {'data-qa': 'vacancy-serp__vacancy_snippet_requirement'})
                if skills_block:
                    skills_text = skills_block.text.strip()
                    # Extract skills separated by commas, semicolons, or dots
                    skills = [skill.strip() for skill in re.split(r'[,;.]', skills_text) if skill.strip()]
                
                # Extract salary information
                salary = "Not specified"
                salary_element = block.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                if salary_element:
                    salary = salary_element.text.strip()
                
                # Extract experience requirements
                experience = "Not specified"
                exp_element = block.find('div', {'data-qa': 'vacancy-serp__vacancy_snippet_requirement'})
                if exp_element:
                    exp_text = exp_element.text.lower()
                    # Look for experience patterns like "1-3 years", "from 3 years", etc.
                    exp_patterns = [
                        r'(\d+[-–]\d+\s+(?:year|years|год|года|лет))',
                        r'(от\s+\d+\s+(?:year|years|год|года|лет))',
                        r'(experience\s+\d+[-–]?\d*\s+(?:year|years|год|года|лет))',
                        r'(опыт\s+\d+[-–]?\d*\s+(?:year|years|год|года|лет))'
                    ]
                    for pattern in exp_patterns:
                        match = re.search(pattern, exp_text, re.IGNORECASE)
                        if match:
                            experience = match.group(1)
                            break
                
                # Extract location
                location = "Not specified"
                location_element = block.find('div', {'data-qa': 'vacancy-serp__vacancy-address'})
                if location_element:
                    location = location_element.text.strip()
                
                # Extract publication date
                publication_date = "Not specified"
                date_element = block.find('span', {'data-qa': 'vacancy-serp__vacancy-date'})
                if date_element:
                    publication_date = date_element.text.strip()
                
                # Create vacancy object with unique ID (constructed from link)
                vacancy_id = link.split('/')[-1]
                
                vacancy = {
                    'id': vacancy_id,
                    'title': title,
                    'company': company,
                    'skills': skills,
                    'link': link,
                    'salary': salary,
                    'experience': experience,
                    'location': location,
                    'publication_date': publication_date,
                    'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                vacancies.append(vacancy)
                
            except Exception as e:
                logging.error(f"Error parsing vacancy: {e}")
                continue
        
        return vacancies

    def save_to_json(self, data: List[Dict], filename: str) -> str:
        """
        Save data to a JSON file.
        
        Args:
            data: The data to save
            filename: The filename to save to
            
        Returns:
            The full path to the saved file
        """
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved data to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Error saving to JSON: {e}")
            return ""

    def load_from_json(self, filepath: str) -> List[Dict]:
        """
        Load data from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            The loaded data
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"Error loading from JSON: {e}")
            return []

    def filter_new_vacancies(self, all_vacancies: List[Dict], new_vacancies: List[Dict]) -> List[Dict]:
        """
        Filter out vacancies that already exist in all_vacancies.
        
        Args:
            all_vacancies: Existing vacancies
            new_vacancies: New vacancies to filter
            
        Returns:
            Filtered list of new vacancies
        """
        existing_ids = {vacancy['id'] for vacancy in all_vacancies}
        return [vacancy for vacancy in new_vacancies if vacancy['id'] not in existing_ids]

    def run_once(self) -> Tuple[List[Dict], List[Dict], List[Dict], str, Optional[str]]:
        """
        Run the scraper once.
        
        Returns:
            Tuple of (all_vacancies, new_vacancies, updated_vacancies, all_vacancies_file, new_vacancies_file)
        """
        logging.info(f"Starting scraping run for query: {self.search_query}")
        all_vacancies = self.load_from_json(self.all_vacancies_file)
        
        # Dictionary to track existing vacancy IDs and their indices
        existing_vacancy_map = {vacancy['id']: idx for idx, vacancy in enumerate(all_vacancies)}
        
        # Track new and updated vacancies
        new_vacancies = []
        updated_vacancies = []
        
        # Scrape each page
        for page in range(self.pages_to_scrape):
            params = {
                'text': self.search_query,
                'page': page,
                'items_on_page': 50
            }
            
            html = self.fetch_html(self.base_url, params)
            if not html:
                logging.warning(f"No HTML content received for page {page}")
                continue
            
            # Parse vacancies from the page
            page_vacancies = self.parse_vacancies(html)
            logging.info(f"Found {len(page_vacancies)} vacancies on page {page}")
            
            for vacancy in page_vacancies:
                vacancy_id = vacancy['id']
                
                if vacancy_id in existing_vacancy_map:
                    # Update existing vacancy
                    idx = existing_vacancy_map[vacancy_id]
                    
                    # Check if the vacancy has new information
                    existing_vacancy = all_vacancies[idx]
                    if (vacancy['title'] != existing_vacancy['title'] or
                        vacancy['company'] != existing_vacancy['company'] or
                        vacancy['salary'] != existing_vacancy.get('salary', 'Not specified') or
                        vacancy['experience'] != existing_vacancy.get('experience', 'Not specified') or
                        vacancy['location'] != existing_vacancy.get('location', 'Not specified') or
                        vacancy['skills'] != existing_vacancy.get('skills', [])):
                        
                        # Keep the original creation timestamp
                        vacancy['created_at'] = existing_vacancy['created_at']
                        # Update the vacancy
                        all_vacancies[idx] = vacancy
                        updated_vacancies.append(vacancy)
                else:
                    # Add as a new vacancy
                    new_vacancies.append(vacancy)
                    existing_vacancy_map[vacancy_id] = len(all_vacancies)
                    all_vacancies.append(vacancy)
            
            # Add a small delay between pages to be respectful to the server
            if page < self.pages_to_scrape - 1:
                time.sleep(2)
        
        # Save all vacancies
        all_vacancies_file = self.save_to_json(all_vacancies, "all_vacancies.json")
        
        # Save new vacancies if there are any
        new_vacancies_file = None
        if new_vacancies:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_vacancies_file = self.save_to_json(new_vacancies, f"new_vacancies_{timestamp}.json")
        
        # Log results
        logging.info(f"Scraping completed: {len(all_vacancies)} total, {len(new_vacancies)} new, {len(updated_vacancies)} updated")
        
        return all_vacancies, new_vacancies, updated_vacancies, all_vacancies_file, new_vacancies_file

    def run(self):
        """
        Run the scraper in a continuous loop.
        """
        logging.info(f"Starting continuous scraping every {self.update_interval} seconds")
        
        while True:
            try:
                # Run once
                _, new_vacancies, updated_vacancies, _, _ = self.run_once()
                
                # Log results
                logging.info(f"Found {len(new_vacancies)} new vacancies and {len(updated_vacancies)} updated vacancies")
                
                # Wait for the next update
                logging.info(f"Waiting {self.update_interval} seconds until next update")
                time.sleep(self.update_interval)
                
            except Exception as e:
                logging.error(f"Error in main scraper loop: {e}")
                # Wait before retrying
                time.sleep(60)

if __name__ == "__main__":
    # Example usage
    scraper = HHScraper(search_query="Python", pages_to_scrape=3)
    scraper.run()
