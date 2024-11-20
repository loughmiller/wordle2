import json
import mysql.connector
from mysql.connector import Error

def load_words_from_json(file_path):
    with open(file_path, 'r') as file:
        words = json.load(file)
    return words

def insert_words_into_database(words):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='wizard',
            database='wordle',
            auth_plugin='mysql_native_password')

        if connection.is_connected():
            cursor = connection.cursor()

            # Find the index of 'zymic'
            zymic_index = words.index('zymic') if 'zymic' in words else len(words)

            # Insert words
            for i, word in enumerate(words):
                is_answer = i > zymic_index
                query = "INSERT INTO words (word, answer) VALUES (%s, %s)"
                cursor.execute(query, (word.upper(), is_answer))

            connection.commit()
            print(f"Successfully inserted {len(words)} words into the database.")

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# Main execution
if __name__ == "__main__":
    file_path = 'wordleDictionary.json'
    words = load_words_from_json(file_path)
    insert_words_into_database(words)