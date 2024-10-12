import random
import json
from itertools import product
import multiprocessing
from functools import partial

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

    possible_feedback = generate_all_wordle_feedback()
    #output all possible feedback count
    # print(len(possible_feedback))

    guesses = GUESSES.copy()
    possible_words = ANSWERS.copy()
    
    for attempt in range(1, 7):
        if not possible_words:
            print("No valid words remaining. Something went wrong.")
            return
        
        # score all guesses
        scores = parallel_score_guesses(guesses, possible_words, possible_feedback)

        # sort guesses by score
        guesses.sort(key=lambda guess: scores[guess])

        # print top 10 guesses
        print("Top 10 guesses:")
        for i, guess in enumerate(guesses[:10]):
            print(f"{i + 1}. {guess} - {scores[guess]}")
        
        print(f"\nAttempt {attempt}")

        print(f"Remaining possible words: {len(possible_words)}")

        # if the number of possible words is less than 11, print them with scores using scores dictionary
        if len(possible_words) < 11:
            print("Remaining possible words:")
            for word in possible_words:
                print(f"{word} - {scores[word]}")

        
        # guess the lowest score
        guess = input("Enter guess: ")

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
