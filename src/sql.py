from datetime import datetime, timedelta
import json
import multiprocessing
import mysql.connector
import random
import requests
from functools import partial
from itertools import product

def load_secrets():
    with open('secrets.json') as f:
        return json.load(f)

def fetch_previous_answers():
    start_date = datetime(2021, 6, 19)
    end_date = datetime.now() - timedelta(days=1) # Current date

    # previous_answers = []
    previous_answers = load_previous_answers()

    # print previous answer count
    print(f"Previous answer count: {len(previous_answers)}")

    last_answer_date = datetime.strptime(previous_answers[-1]['print_date'], '%Y-%m-%d')

    start_date = last_answer_date + timedelta(days=1)

    # print start date
    print(f"Start date: {start_date.strftime('%Y-%m-%d')}")

    current_date = start_date

    while current_date < end_date:
        # print fetch date
        print(f"Fetching data for {current_date.strftime('%Y-%m-%d')}")
        previous_answers += [fetch_previous_answer(current_date)]
        current_date += timedelta(days=1)

    with open('previous_answers.json', 'w') as json_file:
        json.dump(previous_answers, json_file)

    # let's just return the ansers
    answers = []
    for answer in previous_answers:
        answers.append(answer['solution'])

    # print(answers)

    return answers

def fetch_previous_answer(date):
    url = f"https://www.nytimes.com/svc/wordle/v2/{date.strftime('%Y-%m-%d')}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for {date.strftime('%Y-%m-%d')}. Status code: {response.status_code}")
        return None

def load_previous_answers():
    with open('previous_answers.json', 'r') as file:
        return json.load(file)

def generate_join_sql(guess, feedback):
    if len(guess) != 5 or len(feedback) != 5:
        raise ValueError("Guess and feedback must both be 5 characters long")

    if not all(c in 'gy?' for c in feedback):
        raise ValueError("Feedback must only contain 'g', 'y', or '?'")

    tables = []
    remove_double_letters = set()

    for i, (letter, fb) in enumerate(zip(guess.upper(), feedback.lower()), start=1):
        if fb == 'g':
            tables.append(f"{letter}g{i} using (word_id)\n")
        elif fb == 'y':
            tables.append(f"{letter}y{i} using (word_id)\n")
            # if this is the second occurrence of the letter, join with the double letter table unless it's already been joined
            if guess[:i-1].count(letter) > 0 and f"{letter.upper()}{letter.upper()} using (word_id)\n" not in tables:
                tables.append(f"{letter.upper()}{letter.upper()} using (word_id)\n")
        elif fb == '?':
            # if this is the second occurrence of the letter, save the letter for double letter removal
            if guess[:i-1].count(letter) > 0:
                remove_double_letters.add(letter)
            else:
                tables.append(f"{letter.upper()}q using (word_id)\n")
        else:
            raise ValueError(f"Invalid feedback character: {fb}")


    join_clause = " INNER JOIN ".join(tables)

    sql = f"""SELECT count(*) FROM possible_answers w INNER JOIN {join_clause}"""

    if remove_double_letters:
        sql += "\n"
        double_letter_sql = []
        for letter in remove_double_letters:
            double_letter_sql.append(f"NOT EXISTS (SELECT 1 FROM {letter.upper()}{letter.upper()} d WHERE d.word_id = w.word_id)\n")

        sql += "WHERE " + " AND ".join(double_letter_sql)

    return sql + ";"

def sql_score_guess(guess, possible_feedback, cursor):
    total = 0
    valid = 0
    for feedback in possible_feedback:
        # print(feedback)
        sql = generate_join_sql(guess, feedback)
        # if print_sql:
        #     print(sql)
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        if count > 0:
            valid += 1
            total += (count * count)

    return guess, total/valid

def score_guess(guess, possible_answers, possible_feedback):
    # print(guess, len(possible_answers), len(possible_feedback))
    total_score = 0
    valid_feedback = 0

    for feedback in possible_feedback:
        matches = len(filter_words(possible_answers, guess, feedback))
        if matches > 0:
            valid_feedback += 1
            total_score += (matches * matches)
            # if guess == 'slate':
            #     print(guess, feedback, matches)

    if valid_feedback == 0:
        return guess, 0

    return guess, total_score



def parallel_score_guesses(guesses, possible_feedback, cursor):
    # Determine the number of CPU cores to use
    num_cores = multiprocessing.cpu_count()

    # Create a partial function to pass the fixed arguments to the scoring function
    partial_score = partial(sql_score_guess, possible_feedback=possible_feedback, cursor=cursor)

    # Create a pool of workers to score the guesses in parallel
    with multiprocessing.Pool(num_cores) as pool:
        scores = pool.map(partial_score, guesses)

    # print(scores)

    return dict(scores)

def generate_all_wordle_feedback():
    # Define the possible feedback options
    feedback_options = ['g', 'y', '?']  # Green, Yellow, Gray

    # Generate all possible combinations of feedback for a 5-letter word
    all_feedback = list(product(feedback_options, repeat=5))

    # Convert each combination to a string
    all_feedback_strings = [''.join(feedback) for feedback in all_feedback]

    return all_feedback_strings

#
# START HERE
#
def main():

    # Load secrets
    secrets = load_secrets()

    # connect to mysql database
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password=secrets['mysql']['password'],
        database='wordle',
        auth_plugin='mysql_native_password'
    )

    cursor = db.cursor()

    # Fetch the previous guesses from the Wordle website
    # previous_answers = [] #fetch_previous_answers()

    # Load the possible answers into a temporary table from the words table
    cursor.execute("CREATE TEMPORARY TABLE possible_answers AS SELECT word_id FROM words where answer = 1")

    # add indexes to the possible_answers table
    cursor.execute("CREATE INDEX word_id_index ON possible_answers (word_id)")

    # print number of possible answers
    cursor.execute("SELECT count(*) FROM possible_answers")
    print(cursor.fetchone()[0])

    possible_feedback = generate_all_wordle_feedback()
    #output all possible feedback count
    # print(len(possible_feedback))

    sql_score_guess("AAPAS", possible_feedback, True)

    # score all words from the words table
    cursor.execute("SELECT word FROM words")
    words = cursor.fetchall()
    guesses = [word[0] for word in words]
    # for word in words:
    #     print(word[0])
    #     print(sql_score_guess(word[0], possible_feedback))

    # timer for scoring and sorting
    start_time = datetime.now()

    # score all guesses
    scores = parallel_score_guesses(guesses, possible_feedback, cursor)

    # sort guesses by score
    guesses.sort(key=lambda guess: scores[guess])

    # print time taken
    print(f"Timer: {datetime.now() - start_time}")

    # print top 10 guesses
    print("Top 10 guesses:")
    for i, guess in enumerate(guesses[:10]):
        print(f"{i + 1}. {guess} - {scores[guess]}")

    # for attempt in range(1, 7):
    #     if not possible_words:
    #         print("No valid words remaining. Something went wrong.")
    #         return

    #     # score all guesses
    #     scores = parallel_score_guesses(guesses, possible_words, possible_feedback)

    #     # sort guesses by score
    #     guesses.sort(key=lambda guess: scores[guess])

    #     # print top 10 guesses
    #     print("Top 10 guesses:")
    #     for i, guess in enumerate(guesses[:10]):
    #         print(f"{i + 1}. {guess} - {scores[guess]}")

    #     print(f"\nAttempt {attempt}")

    #     print(f"Remaining possible words: {len(possible_words)}")

    #     # if the number of possible words is less than 11, print them with scores using scores dictionary
    #     if len(possible_words) < 11:
    #         print("Remaining possible words:")
    #         for word in possible_words:
    #             print(f"{word} - {scores[word]}")

    #     while True:
    #         # allow user to enter guess
    #         guess = input("Enter guess: ")

    #         # check if the guess is valid
    #         if guess not in GUESSES:
    #             print("Invalid guess. Please try again.")
    #         else:
    #             break

    #     feedback = input("Enter feedback (G for Green, Y for Yellow, ? for Gray): ").upper()

    #     if feedback == "GGGGG":
    #         print(f"Solved in {attempt} attempts!")
    #         return

    #     possible_words = filter_words(possible_words, guess, feedback)

    # print("Failed to solve in 6 attempts.")

    # Close the MySQL connection
    cursor.close()
    db.close()

if __name__ == '__main__':
    # Uncomment the next line if using PyInstaller or similar
    # multiprocessing.freeze_support()
    main()