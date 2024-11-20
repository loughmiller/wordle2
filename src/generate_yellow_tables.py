import string

# Initialize the base for creating SQL
sql_statements = []

# Generate SQL for each letter (A-Z) and position (1-5)
for letter in string.ascii_uppercase:
    for position in range(1, 6):
        table_name = f"{letter}y{position}"
        sql = f"CREATE TABLE {table_name} AS\n"
        sql += f"SELECT word_id FROM words\n"
        sql += f"WHERE word LIKE '%{letter}%'\n"
        sql += f"  AND word NOT LIKE '{'_' * (position - 1)}{letter}%';\n"
        sql += f"ALTER TABLE {table_name} ADD PRIMARY KEY (word_id);"
        sql_statements.append(sql)

# Join all SQL statements with newline
full_sql_script = "\n\n".join(sql_statements)

# Print the SQL script
print(full_sql_script)

# Optionally, you can save the SQL script to a file
# with open('create_tables_script.sql', 'w') as f:
#     f.write(full_sql_script)