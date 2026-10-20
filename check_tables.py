
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="carbon_db"
    )

try:
    connection = get_connection()
    cursor = connection.cursor()

    print("MySQL connected successfully!")

    # Display all tables
    cursor.execute("SHOW TABLES")
    print("\nTABLES IN carbon_db:")
    for table in cursor.fetchall():
        print(table[0])

    # Check the structure of each table
    tables = [
        "users",
        "activities",
        "carbon_emissions",
        "recommendations"
    ]

    for table in tables:
        print("\n" + "=" * 40)
        print("TABLE:", table)
        print("=" * 40)

        cursor.execute(f"DESCRIBE `{table}`")

        for column in cursor.fetchall():
            print(column)

    cursor.close()
    connection.close()

except mysql.connector.Error as error:
    print("MySQL Error:", error)
