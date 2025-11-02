import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Vyasxdxd@17',
        database='robinhood_db'
    )
    return conn
