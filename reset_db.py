import mysql.connector

def reset_database():
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456"
    )
    cursor = conn.cursor()

    # Drop database if exists
    cursor.execute("DROP DATABASE IF EXISTS charity_platform")
    print("Database has been dropped")

    # Close connection
    cursor.close()
    conn.close()

    print("Database reset completed, please run setup.py to recreate the database")

if __name__ == "__main__":
    reset_database()
