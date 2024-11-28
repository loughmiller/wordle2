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
            # if this is the second occurrence of the letter, join with the double letter table
            if guess[:i-1].count(letter) > 0:
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

    sql = f"""SELECT count(*) FROM words w INNER JOIN {join_clause}"""

    if remove_double_letters:
        sql += "\n"
        for letter in remove_double_letters:
            sql += f"WHERE NOT EXISTS (SELECT 1 FROM {letter.upper()}{letter.upper()} d WHERE d.word_id = w.word_id)\n"

    return sql + ";"

# Example usage
guess = "SLATE"
feedback = "y????"

try:
    sql = generate_join_sql(guess, feedback)
    print(sql)
except ValueError as e:
    print(f"Error: {e}")