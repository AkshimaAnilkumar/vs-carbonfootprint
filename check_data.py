
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin123",
    database="carbon_db"
)

cursor = connection.cursor()

tables = [
    "users",
    "activities",
    "carbon_emissions",
    "recommendations",
    "predictions"
]

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} records")

cursor.close()
connection.close()
