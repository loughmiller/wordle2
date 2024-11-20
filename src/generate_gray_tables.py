import string

def generate_sql_statements():
    sql_statements = []

    # Generate tables for words not containing specific letters (Aq through Zq)
    for letter in string.ascii_lowercase:
        table_name = f"{letter.upper()}q"
        sql = f"""CREATE TABLE {table_name} AS
SELECT word_id
FROM words
WHERE word NOT LIKE '%{letter}%';

ALTER TABLE {table_name} ADD PRIMARY KEY (word_id);
"""
        sql_statements.append(sql)

    return "\n".join(sql_statements)

# Generate and print the SQL statements
print(generate_sql_statements())

# Optionally, save the SQL statements to a file
# with open('create_tables_script.sql', 'w') as f:
#     f.write(generate_sql_statements())