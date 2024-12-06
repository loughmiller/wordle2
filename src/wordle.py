from datetime import datetime, timedelta
import json
import multiprocessing
import random
import requests
from functools import partial
from itertools import product

# Assuming your JSON data is stored in a file named 'words.json'
with open('wordleDictionary.json', 'r') as file:
    GUESSES = json.load(file)

# print the first 10 words to make sure the file was loaded correctly
# print(len(GUESSES))

# possible answers only appear in GUESSES after the work zymic
# slice the array after the word zymic
ANSWERS = GUESSES[GUESSES.index('zymic') + 1:]

# print(len(ANSWERS))

# use smaller dataset for testing
# GUESSES = ANSWERS
# ANSWERS = GUESSES
# print(len(GUESSES))

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
        previous_answers += [fetch_answer(current_date)]
        current_date += timedelta(days=1)

    with open('previous_answers.json', 'w') as json_file:
        json.dump(previous_answers, json_file)

    # let's just return the ansers
    answers = []
    for answer in previous_answers:
        answers.append(answer['solution'])

    # print(answers)

    return answers

# API result example: {'id': 2326, 'solution': 'primp', 'print_date': '2024-11-13', 'days_since_launch': 1243, 'editor': 'Tracy Bennett'}
def fetch_answer(date):
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

def filter_words(words, guess, feedback):
    new_words = []
    for word in words:
        if len(word) != len(guess):
            continue

        # Count the occurrences of each letter in the word
        word_letter_count = {}
        for letter in word:
            word_letter_count[letter] = word_letter_count.get(letter, 0) + 1

        # Check if the word matches the feedback
        match = True
        for i, (g, f) in enumerate(zip(guess, feedback)):
            if f == 'G' and word[i] != g:
                match = False
                break
            elif f == 'Y':
                if g not in word or word[i] == g:
                    match = False
                    break
                word_letter_count[g] -= 1
            elif f == '?' and g in word:
                # Check if all occurrences of this letter are accounted for
                remaining = sum(1 for j, letter in enumerate(word) if letter == g and feedback[j] in 'GY')
                if word_letter_count[g] > remaining:
                    match = False
                    break

        if match:
            new_words.append(word)

    return new_words

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

    return guess, total_score/valid_feedback

def parallel_score_guesses(guesses, possible_answers, possible_feedback):
    # Determine the number of CPU cores to use
    num_cores = multiprocessing.cpu_count()

    # Create a partial function to pass the fixed arguments to the scoring function
    partial_score = partial(score_guess, possible_answers=possible_answers, possible_feedback=possible_feedback)

    # Create a pool of workers to score the guesses in parallel
    with multiprocessing.Pool(num_cores) as pool:
        scores = pool.map(partial_score, guesses)

    # print(scores)

    return dict(scores)

def generate_all_wordle_feedback():
    # Define the possible feedback options
    feedback_options = ['G', 'Y', '?']  # Green, Yellow, Gray

    # Generate all possible combinations of feedback for a 5-letter word
    all_feedback = list(product(feedback_options, repeat=5))

    # Convert each combination to a string
    all_feedback_strings = [''.join(feedback) for feedback in all_feedback]

    return all_feedback_strings

def main():

    # Fetch the previous guesses from the Wordle website
    previous_answers = fetch_previous_answers()

    # Fetch today's answer in case they add a new word!
    today_answer = fetch_answer(datetime.now())

    #print today's answer
    # print(today_answer['solution'])

    possible_feedback = generate_all_wordle_feedback()
    #output all possible feedback count
    # print(len(possible_feedback))

    guesses = GUESSES.copy()
    possible_words = ANSWERS.copy()

    # if today's answer is not in the possible words, add it
    if today_answer['solution'] not in possible_words:
        print("A word was added!")
        possible_words.append(today_answer['solution'])

    # remove previous answers from possible words
    for answer in previous_answers:
        if answer in possible_words:
            possible_words.remove(answer)

    for attempt in range(1, 7):
        if not possible_words:
            print("No valid words remaining. Something went wrong.")
            return

        # timer for scoring and sorting
        start_time = datetime.now()

        # score all guesses
        scores = parallel_score_guesses(guesses, possible_words, possible_feedback)

        # sort guesses by score
        guesses.sort(key=lambda guess: scores[guess])

        # print time taken
        print(f"Timer: {datetime.now() - start_time}")

        # print top 10 guesses
        print("Top 10 guesses:")
        for i, guess in enumerate(guesses[:10]):
            print(f"{i + 1}. {guess} - {scores[guess]}")

        print(f"\nAttempt {attempt}")

        print(f"Remaining possible words: {len(possible_words)}")

        # display the top 10 remaining possible words

        possible_words.sort(key=lambda word: scores[word])

        print("Remaining possible words:")
        for i, word in enumerate(possible_words[:10]):
            print(f"{i + 1}. {word} - {scores[word]}")


        while True:
            # allow user to enter guess
            guess = input("Enter guess: ")

            # check if the guess is valid
            if guess not in GUESSES:
                print("Invalid guess. Please try again.")
            else:
                break

        feedback = input("Enter feedback (G for Green, Y for Yellow, ? for Gray): ").upper()

        if feedback == "GGGGG":
            print(f"Solved in {attempt} attempts!")
            return

        possible_words = filter_words(possible_words, guess, feedback)

    print("Failed to solve in 6 attempts.")

if __name__ == '__main__':
    # Uncomment the next line if using PyInstaller or similar
    # multiprocessing.freeze_support()
    main()
