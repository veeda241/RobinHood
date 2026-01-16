"""
RobinHood AI - Database Reset Script
This recreates the users table with the correct structure
"""

import mysql.connector
from mysql.connector import errorcode

DB_NAME = 'robinhood_db'

def setup_database():
    try:
        # Connect to MySQL
        cnx = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Vyasxdxd@17'
        )
        cursor = cnx.cursor()
        
        # Create database if not exists
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' ready.")
        except mysql.connector.Error as err:
            print(f"Error creating database: {err}")
            return
        
        # Use the database
        cursor.execute(f"USE {DB_NAME}")
        
        # Drop existing table and recreate
        print("Dropping existing users table if exists...")
        cursor.execute("DROP TABLE IF EXISTS notices")
        cursor.execute("DROP TABLE IF EXISTS payments")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # Create users table with correct structure
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                user_id VARCHAR(50) PRIMARY KEY,
                declared_income DECIMAL(15, 2) NOT NULL DEFAULT 0,
                tax_paid DECIMAL(15, 2) NOT NULL DEFAULT 0,
                flagged BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("Users table created successfully!")
        
        # Create notices table
        print("Creating notices table...")
        cursor.execute("""
            CREATE TABLE notices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                notice_type ENUM('reminder', 'warning', 'final', 'penalty') NOT NULL,
                amount_due DECIMAL(15, 2) NOT NULL,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        print("Notices table created successfully!")
        
        # Create payments table
        print("Creating payments table...")
        cursor.execute("""
            CREATE TABLE payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                reference_no VARCHAR(100),
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        print("Payments table created successfully!")
        
        # Insert sample data
        print("\nInserting sample data...")
        sample_users = [
            ('TXP001', 500000, 10000, False),
            ('TXP002', 800000, 25000, False),
            ('TXP003', 1200000, 45000, False),
            ('TXP004', 1500000, 90000, False),
            ('TXP005', 2000000, 100000, True),
            ('TXP006', 350000, 0, False),
            ('TXP007', 950000, 55000, False),
            ('TXP008', 600000, 15000, False),
        ]
        
        for user in sample_users:
            cursor.execute(
                "INSERT INTO users (user_id, declared_income, tax_paid, flagged) VALUES (%s, %s, %s, %s)",
                user
            )
            print(f"  Added user: {user[0]}")
        
        cnx.commit()
        print("\n" + "="*50)
        print("Database setup complete!")
        print("="*50)
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"\nTotal users in database: {count}")
        
        cursor.close()
        cnx.close()
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Wrong username or password")
        else:
            print(f"Error: {err}")

if __name__ == '__main__':
    print("="*50)
    print("RobinHood AI - Database Setup")
    print("="*50 + "\n")
    setup_database()
