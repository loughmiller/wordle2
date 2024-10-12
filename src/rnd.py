import random
import json

# Assuming your JSON data is stored in a file named 'words.json'
with open('wordleDictionary.json', 'r') as file:
    GUESSES = json.load(file)

# print the first 10 words to make sure the file was loaded correctly
print(GUESSES[:10])

# possible answers only appear in GUESSES after the work zymic
# slice the array after the word zymic
ANSWERS = GUESSES[GUESSES.index('zymic') + 1:]

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

def score_guess(guess, possible_answers):
    total_score = 0

    for answer in possible_answers:
        score = 0
        used_positions = set()
        

        # First, check for green letters (exact matches)
        for i, (g, a) in enumerate(zip(guess, answer)):
            if g == a:
                score += 2
                used_positions.add(i)

        # Then, check for yellow letters (correct letter, wrong position)
        for i, g in enumerate(guess):
            if i not in used_positions:
                for j, a in enumerate(answer):
                    if j not in used_positions and g == a:
                        score += 1
                        used_positions.add(j)
                        break

        total_score += score    
        
    return total_score

def play_wordle():
    guesses = GUESSES.copy()
    possible_words = ANSWERS.copy()
    
    for attempt in range(1, 7):
        if not possible_words:
            print("No valid words remaining. Something went wrong.")
            return
        
        # score all guesses
        scores = {}
        for guess in guesses:
            scores[guess] = score_guess(guess, possible_words)

        # sort guesses by score
        guesses.sort(key=lambda guess: scores[guess], reverse=True)

        # print top 10 guesses
        print("Top 10 guesses:")
        for i, guess in enumerate(guesses[:10]):
            print(f"{i + 1}. {guess} - {scores[guess]}")
        
        guess = random.choice(guesses)
        print(f"\nAttempt {attempt}: {guess}")
        
        feedback = input("Enter feedback (G for Green, Y for Yellow, ? for Gray): ")
        
        if feedback == "GGGGG":
            print(f"Solved in {attempt} attempts!")
            return
        
        possible_words = filter_words(possible_words, guess, feedback)
        print(f"Remaining possible words: {len(possible_words)}")

        if len(possible_words) < 11:
            print(possible_words)
    
    print("Failed to solve in 6 attempts.")

play_wordle()
