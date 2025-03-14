import sqlite3
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, db_name="vacancies.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_name = db_name
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            self.create_tables()
            logging.info(f"База данных {db_name} успешно инициализирована")
        except Exception as e:
            logging.error(f"Ошибка при инициализации базы данных: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        # Create vacancies table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS vacancies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            link TEXT NOT NULL,
            skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create subscriptions table for users who want to receive updates
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
        logging.info("Таблицы в базе данных созданы или уже существуют")
    
    def add_vacancy(self, vacancy):
        """Add a vacancy to the database if it doesn't exist"""
        try:
            # Convert skills list to JSON string if it exists
            skills_json = json.dumps(vacancy.get('skills', []), ensure_ascii=False) if 'skills' in vacancy else None
            
            # Insert vacancy data
            self.cursor.execute('''
            INSERT OR IGNORE INTO vacancies (id, title, company, link, skills, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                vacancy['id'],
                vacancy['title'],
                vacancy['company'],
                vacancy['link'],
                skills_json,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка при добавлении вакансии в базу данных: {e}")
            return False
    
    def add_multiple_vacancies(self, vacancies):
        """Add multiple vacancies to the database"""
        added_count = 0
        for vacancy in vacancies:
            if self.add_vacancy(vacancy):
                added_count += 1
        logging.info(f"Добавлено {added_count} новых вакансий в базу данных")
        return added_count
    
    def get_vacancy_by_id(self, vacancy_id):
        """Get a vacancy by its ID"""
        try:
            self.cursor.execute('SELECT * FROM vacancies WHERE id = ?', (vacancy_id,))
            vacancy = self.cursor.fetchone()
            if vacancy:
                return self._vacancy_to_dict(vacancy)
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении вакансии по ID: {e}")
            return None
    
    def search_vacancies(self, keyword, limit=10):
        """Search vacancies by keyword in title or skills"""
        try:
            query = '''
            SELECT * FROM vacancies 
            WHERE title LIKE ? OR skills LIKE ? 
            ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
                
            self.cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
            vacancies = self.cursor.fetchall()
            return [self._vacancy_to_dict(vacancy) for vacancy in vacancies]
        except Exception as e:
            logging.error(f"Ошибка при поиске вакансий: {e}")
            return []
    
    def get_latest_vacancies(self, limit=5):
        """Get the latest vacancies added to the database"""
        try:
            self.cursor.execute('''
            SELECT * FROM vacancies 
            ORDER BY created_at DESC 
            LIMIT ?
            ''', (limit,))
            vacancies = self.cursor.fetchall()
            return [self._vacancy_to_dict(vacancy) for vacancy in vacancies]
        except Exception as e:
            logging.error(f"Ошибка при получении последних вакансий: {e}")
            return []
    
    def _vacancy_to_dict(self, vacancy_tuple):
        """Convert a vacancy tuple from the database to a dictionary"""
        id, title, company, link, skills_json, created_at = vacancy_tuple
        
        # Parse skills JSON if it exists
        skills = json.loads(skills_json) if skills_json else []
        
        return {
            'id': id,
            'title': title,
            'company': company,
            'link': link,
            'skills': skills,
            'created_at': created_at
        }
    
    def add_subscription(self, user_id, keywords=None):
        """Add or update a user subscription"""
        try:
            keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords else None
            
            self.cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (user_id, keywords, created_at)
            VALUES (?, ?, ?)
            ''', (
                user_id,
                keywords_json,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            self.conn.commit()
            logging.info(f"Пользователь {user_id} подписался на обновления")
            return True
        except Exception as e:
            logging.error(f"Ошибка при добавлении подписки: {e}")
            return False
    
    def remove_subscription(self, user_id):
        """Remove a user subscription"""
        try:
            self.cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            self.conn.commit()
            logging.info(f"Пользователь {user_id} отписался от обновлений")
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении подписки: {e}")
            return False
    
    def get_all_subscribers(self):
        """Get all subscribers"""
        try:
            self.cursor.execute('SELECT user_id, keywords FROM subscriptions')
            subscribers = self.cursor.fetchall()
            result = []
            for user_id, keywords_json in subscribers:
                keywords = json.loads(keywords_json) if keywords_json else None
                result.append({'user_id': user_id, 'keywords': keywords})
            return result
        except Exception as e:
            logging.error(f"Ошибка при получении списка подписчиков: {e}")
            return []
    
    def count_vacancies(self):
        """Count the total number of vacancies in the database"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM vacancies')
            return self.cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Ошибка при подсчете вакансий: {e}")
            return 0
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logging.info("Соединение с базой данных закрыто") 