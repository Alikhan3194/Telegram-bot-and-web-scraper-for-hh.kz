import sqlite3
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='db.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseManager:
    def __init__(self, db_name="vacancies.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_name = db_name
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            self.create_tables()
            logging.info(f"Connected to database: {db_name}")
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
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
            salary TEXT,
            experience TEXT,
            location TEXT,
            publication_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create subscriptions table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            keywords TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create notifications table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vacancy_id TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vacancy_id) REFERENCES vacancies (id),
            UNIQUE(user_id, vacancy_id)
        )
        ''')
        
        self.conn.commit()
        logging.info("Database tables created or already exist")
    
    def add_vacancy(self, vacancy):
        """Add a vacancy to the database if it doesn't exist"""
        try:
            # Convert skills list to JSON string if it exists
            skills_json = json.dumps(vacancy.get('skills', []), ensure_ascii=False) if 'skills' in vacancy else None
            
            # Insert vacancy data
            self.cursor.execute('''
            INSERT OR IGNORE INTO vacancies (id, title, company, link, skills, salary, experience, location, publication_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vacancy['id'],
                vacancy['title'],
                vacancy['company'],
                vacancy['link'],
                skills_json,
                vacancy.get('salary', 'Not specified'),
                vacancy.get('experience', 'Not specified'),
                vacancy.get('location', 'Not specified'),
                vacancy.get('publication_date', 'Unknown date'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            self.conn.commit()
            
            # Check if the vacancy was actually inserted
            changes = self.cursor.rowcount
            if changes > 0:
                logging.info(f"Added vacancy to database: {vacancy['title']} at {vacancy['company']}")
                return True
            else:
                logging.info(f"Vacancy already exists in database: {vacancy['title']}")
                return False
        except Exception as e:
            logging.error(f"Error adding vacancy to database: {e}")
            return False
    
    def add_multiple_vacancies(self, vacancies):
        """Add multiple vacancies to the database"""
        added_count = 0
        for vacancy in vacancies:
            if self.add_vacancy(vacancy):
                added_count += 1
        logging.info(f"Added {added_count} new vacancies to database")
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
            logging.error(f"Error getting vacancy by ID: {e}")
            return None
    
    def get_vacancies_by_keyword(self, keyword, limit=None):
        """Get vacancies that match a keyword in title or skills"""
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
            result = [self._vacancy_to_dict(vacancy) for vacancy in vacancies]
            logging.info(f"Found {len(result)} vacancies matching keyword: {keyword}")
            return result
        except Exception as e:
            logging.error(f"Error searching vacancies by keyword: {e}")
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
            result = [self._vacancy_to_dict(vacancy) for vacancy in vacancies]
            logging.info(f"Retrieved {len(result)} latest vacancies")
            return result
        except Exception as e:
            logging.error(f"Error getting latest vacancies: {e}")
            return []
    
    def _vacancy_to_dict(self, vacancy_tuple):
        """Convert a vacancy tuple from the database to a dictionary"""
        id, title, company, link, skills_json, salary, experience, location, publication_date, created_at = vacancy_tuple
        
        # Parse skills JSON if it exists
        skills = json.loads(skills_json) if skills_json else []
        
        return {
            'id': id,
            'title': title,
            'company': company,
            'link': link,
            'skills': skills,
            'salary': salary,
            'experience': experience,
            'location': location,
            'publication_date': publication_date,
            'created_at': created_at
        }
    
    def add_subscription(self, user_id, keywords=None):
        """Add or update a user subscription"""
        try:
            keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords else None
            
            self.cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (user_id, keywords, active, created_at)
            VALUES (?, ?, 1, ?)
            ''', (
                user_id,
                keywords_json,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            self.conn.commit()
            logging.info(f"User {user_id} subscribed to vacancy updates")
            return True
        except Exception as e:
            logging.error(f"Error adding subscription: {e}")
            return False
    
    def remove_subscription(self, user_id):
        """Remove a user subscription by setting active to 0"""
        try:
            self.cursor.execute('''
            UPDATE subscriptions SET active = 0 WHERE user_id = ?
            ''', (user_id,))
            self.conn.commit()
            logging.info(f"User {user_id} unsubscribed from vacancy updates")
            return True
        except Exception as e:
            logging.error(f"Error removing subscription: {e}")
            return False
    
    def get_all_active_subscribers(self):
        """Get all active subscribers"""
        try:
            self.cursor.execute('SELECT user_id, keywords FROM subscriptions WHERE active = 1')
            subscribers = self.cursor.fetchall()
            result = []
            for user_id, keywords_json in subscribers:
                keywords = json.loads(keywords_json) if keywords_json else None
                result.append({'user_id': user_id, 'keywords': keywords})
            logging.info(f"Retrieved {len(result)} active subscribers")
            return result
        except Exception as e:
            logging.error(f"Error getting active subscribers: {e}")
            return []
    
    def add_notification(self, user_id, vacancy_id):
        """Record that a notification was sent to a user for a specific vacancy"""
        try:
            self.cursor.execute('''
            INSERT OR IGNORE INTO notifications (user_id, vacancy_id, sent_at)
            VALUES (?, ?, ?)
            ''', (
                user_id,
                vacancy_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding notification record: {e}")
            return False
    
    def get_unsent_vacancies_for_user(self, user_id, limit=5):
        """Get vacancies that haven't been sent to the user yet"""
        try:
            self.cursor.execute('''
            SELECT * FROM vacancies 
            WHERE id NOT IN (
                SELECT vacancy_id FROM notifications WHERE user_id = ?
            )
            ORDER BY created_at DESC
            LIMIT ?
            ''', (user_id, limit))
            
            vacancies = self.cursor.fetchall()
            result = [self._vacancy_to_dict(vacancy) for vacancy in vacancies]
            logging.info(f"Found {len(result)} unsent vacancies for user {user_id}")
            return result
        except Exception as e:
            logging.error(f"Error getting unsent vacancies: {e}")
            return []
    
    def count_vacancies(self):
        """Count the total number of vacancies in the database"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM vacancies')
            count = self.cursor.fetchone()[0]
            logging.info(f"Total vacancies in database: {count}")
            return count
        except Exception as e:
            logging.error(f"Error counting vacancies: {e}")
            return 0
    
    def get_stats(self):
        """Get various statistics about the database"""
        try:
            stats = {}
            
            # Total vacancies
            self.cursor.execute('SELECT COUNT(*) FROM vacancies')
            stats['total_vacancies'] = self.cursor.fetchone()[0]
            
            # Vacancies by company
            self.cursor.execute('''
            SELECT company, COUNT(*) as count 
            FROM vacancies 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 5
            ''')
            stats['companies'] = [{'name': row[0], 'count': row[1]} for row in self.cursor.fetchall()]
            
            # Most common skills
            self.cursor.execute('SELECT skills FROM vacancies')
            all_skills = {}
            for (skills_json,) in self.cursor.fetchall():
                if skills_json:
                    skills = json.loads(skills_json)
                    for skill in skills:
                        all_skills[skill] = all_skills.get(skill, 0) + 1
            
            stats['skills'] = [{'name': skill, 'count': count} 
                              for skill, count in sorted(all_skills.items(), 
                                                        key=lambda x: x[1], 
                                                        reverse=True)[:10]]
            
            # Total subscribers
            self.cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE active = 1')
            stats['active_subscribers'] = self.cursor.fetchone()[0]
            
            logging.info(f"Retrieved database statistics")
            return stats
        except Exception as e:
            logging.error(f"Error getting database statistics: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    # Simple test
    db = DatabaseManager()
    print(f"Total vacancies in database: {db.count_vacancies()}")
    db.close() 
