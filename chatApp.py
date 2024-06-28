import mysql.connector
import configparser

def create_tables():
    # Initialize ConfigParser object and read the 'config.ini' file
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Get db settings
    db_config = {key: config.get('DB_CREDENTIALS', value).strip('"') for key, value in {
        'host': 'dbhost',
        'user': 'dbuser',
        'password': 'mypass',
        'database': 'dbname'
    }.items()}

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
    """)
   
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        conversation_id INT,
        role ENUM('user', 'assistant') NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)
    db.commit()
    db.close()

if __name__ == "__main__":
    create_tables()