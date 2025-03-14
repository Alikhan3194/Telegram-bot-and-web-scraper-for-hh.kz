import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class HHScraper:
    def __init__(self, search_query="Python", region="160"):  # 160 is for Almaty
        self.search_query = search_query
        self.region = region
        self.base_url = "https://hh.kz/search/vacancy"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept': '*/*'
        }
        self.all_vacancies = []
        self.new_vacancies = []
        self.old_vacancies = []
        
        # Create output directory if it doesn't exist
        self.output_dir = "vacancies"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        logging.info(f"Инициализирован скрапер для поиска '{search_query}' в регионе {region}")

    def get_page(self, page=0):
        """Get HTML content of a specific page"""
        params = {
            "text": self.search_query,
            "area": self.region,
            "page": page
        }
        
        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            logging.info(f"Успешно получена страница {page}")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении страницы {page}: {e}")
            return None
            
    def get_vacancy_details(self, vacancy_url):
        """Get detailed information about a specific vacancy"""
        try:
            response = requests.get(vacancy_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract skills
            skills = []
            skills_block = soup.find('div', {'class': 'bloko-tag-list'})
            
            if skills_block:
                skill_tags = skills_block.find_all('div', {'class': 'bloko-tag__section'})
                for tag in skill_tags:
                    skills.append(tag.text.strip())
            
            logging.info(f"Получены детали вакансии: {vacancy_url}, найдено {len(skills)} навыков")
            return {
                'skills': skills
            }
            
        except Exception as e:
            logging.error(f"Ошибка при получении деталей вакансии {vacancy_url}: {e}")
            return {'skills': []}

    def parse_vacancies(self, html):
        """Parse HTML to extract vacancy information"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        vacancies_found = []
        
        # Find all vacancy items
        vacancy_items = soup.find_all('div', {'class': 'vacancy-serp-item__layout'})
        logging.info(f"Найдено {len(vacancy_items)} вакансий на странице")
        
        for item in vacancy_items:
            try:
                # Extract vacancy title and link
                title_element = item.find('a', {'class': 'serp-item__title'})
                if not title_element:
                    continue
                    
                title = title_element.text.strip()
                link = title_element['href'].split('?')[0]  # Remove query parameters
                
                # Extract company name
                company_element = item.find('div', {'class': 'vacancy-serp-item__meta-info-company'})
                company = company_element.text.strip() if company_element else "Unknown company"
                
                # Create vacancy object
                vacancy = {
                    "title": title,
                    "company": company,
                    "link": link,
                    "id": link.split('/')[-1]  # Extract vacancy ID from link
                }
                
                # Get detailed information including skills
                details = self.get_vacancy_details(link)
                vacancy.update(details)
                
                vacancies_found.append(vacancy)
            except Exception as e:
                logging.error(f"Ошибка при парсинге вакансии: {e}")
                continue
                
        return vacancies_found
        
    def scrape_all_pages(self, max_pages=20):
        """Scrape multiple pages of search results"""
        all_vacancies = []
        
        for page in range(max_pages):
            logging.info(f"Скрапинг страницы {page}...")
            html = self.get_page(page)
            
            if not html:
                logging.warning(f"Не удалось получить страницу {page}, прерывание")
                break
                
            vacancies = self.parse_vacancies(html)
            
            if not vacancies:
                logging.info(f"Нет вакансий на странице {page}, прерывание")
                break
                
            all_vacancies.extend(vacancies)
            
            # Check if we've reached the last page
            soup = BeautifulSoup(html, 'html.parser')
            if not soup.find('a', {'data-qa': 'pager-next'}):
                logging.info("Достигнута последняя страница")
                break
                
            # Be nice to the server
            time.sleep(1)
            
        logging.info(f"Всего найдено {len(all_vacancies)} вакансий")
        return all_vacancies

    def identify_new_vacancies(self, current_vacancies):
        """Identify new vacancies by comparing with previous results"""
        if not self.all_vacancies:
            logging.info("Первый запуск, все вакансии считаются новыми")
            return current_vacancies, []
            
        # Get IDs of existing vacancies
        existing_ids = {v["id"] for v in self.all_vacancies}
        
        # Separate new and old vacancies
        new_vacancies = [v for v in current_vacancies if v["id"] not in existing_ids]
        old_vacancies = [v for v in current_vacancies if v["id"] in existing_ids]
        
        logging.info(f"Найдено {len(new_vacancies)} новых и {len(old_vacancies)} старых вакансий")
        return new_vacancies, old_vacancies
        
    def save_to_json(self, vacancies, filename):
        """Save vacancies to a JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vacancies, f, ensure_ascii=False, indent=2)
        logging.info(f"Сохранено {len(vacancies)} вакансий в файл {filepath}")

    def run(self, interval=600):
        """Run the scraper at specified intervals"""
        try:
            while True:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                logging.info(f"Начало скрапинга в {timestamp}")
                
                # Scrape all pages
                current_vacancies = self.scrape_all_pages()
                
                # Identify new and old vacancies
                self.new_vacancies, self.old_vacancies = self.identify_new_vacancies(current_vacancies)
                
                # Save all current vacancies
                self.save_to_json(current_vacancies, f"all_vacancies_{timestamp}.json")
                
                # Save new vacancies if any
                if self.new_vacancies:
                    self.save_to_json(self.new_vacancies, f"new_vacancies_{timestamp}.json")
                
                # Save old vacancies if any
                if self.old_vacancies:
                    self.save_to_json(self.old_vacancies, f"old_vacancies_{timestamp}.json")
                
                # Update all vacancies list
                self.all_vacancies = current_vacancies
                
                logging.info(f"Найдено {len(current_vacancies)} вакансий всего")
                logging.info(f"Новых вакансий: {len(self.new_vacancies)}")
                logging.info(f"Старых вакансий: {len(self.old_vacancies)}")
                logging.info(f"Ожидание {interval} секунд до следующего обновления...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logging.info("Скрапинг остановлен пользователем")
        except Exception as e:
            logging.error(f"Ошибка в скрапере: {e}")

    def run_once(self):
        """Run the scraper once and return the results"""
        logging.info("Запуск одноразового скрапинга...")
        current_vacancies = self.scrape_all_pages()
        self.new_vacancies, self.old_vacancies = self.identify_new_vacancies(current_vacancies)
        self.all_vacancies = current_vacancies
        
        logging.info(f"Найдено {len(current_vacancies)} вакансий всего")
        logging.info(f"Новых вакансий: {len(self.new_vacancies)}")
        logging.info(f"Старых вакансий: {len(self.old_vacancies)}")
        
        return current_vacancies, self.new_vacancies, self.old_vacancies

if __name__ == "__main__":
    # Create and run the scraper
    logging.info("Парсер запущен...")
    scraper = HHScraper(search_query="Python")
    scraper.run(interval=600)  # Update every 600 seconds (10 minutes) 