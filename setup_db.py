import mysql.connector
from mysql.connector import errorcode

DB_NAME = 'robinhood_db'

TABLES = {}
TABLES['users'] = (
    "CREATE TABLE `users` ("
    "  `user_id` varchar(255) NOT NULL,"
    "  `declared_income` decimal(10,2) NOT NULL,"
    "  `tax_paid` decimal(10,2) NOT NULL DEFAULT '0.00',"
    "  `flagged` tinyint(1) NOT NULL DEFAULT '0',"
    "  PRIMARY KEY (`user_id`)"
    ") ENGINE=InnoDB")

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

def create_tables(cursor):
    cursor.execute("USE {}".format(DB_NAME))
    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

if __name__ == '__main__':
    try:
        cnx = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Vyasxdxd@17'
        )
        cursor = cnx.cursor()
        try:
            cursor.execute("USE {}".format(DB_NAME))
        except mysql.connector.Error as err:
            print("Database {} does not exists.".format(DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                print("Database {} created successfully.".format(DB_NAME))
                cnx.database = DB_NAME
            else:
                print(err)
                exit(1)
        create_tables(cursor)
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        print("Database setup complete.")
