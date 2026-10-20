
import mysql.connector

def check_predictions():
    connection = None

    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin123",
            database="carbon_db"
        )

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                prediction_id,
                user_id,
                predicted_month,
                predicted_co2,
                emission_level,
                created_at
            FROM predictions
            ORDER BY prediction_id DESC
        """)

        records = cursor.fetchall()

        print("\n========== SAVED AI PREDICTIONS ==========\n")

        if records:
            for record in records:
                print(record)
        else:
            print("No predictions saved yet.")

        cursor.close()

    except mysql.connector.Error as error:
        print("Database error:", error)

    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    check_predictions()
