import sqlite3
import pandas as pd
import os
from openai import OpenAI
import re
db_path = 'chat_sheet.db'
error_log = 'error_logs.txt'
def connect_db():
    return sqlite3.connect(db_path)

def log_error(message):
    with open(error_log, 'a') as f:
        f.write(message + '\n')

def load_csv_to_sqlite(csv_path , table_name, conn):
    try:
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists='fail', index=False)
        print(f'Loaded {csv_path} to {table_name}! ')
    except ValueError as e:
        print(f'Table {table_name} already exists')
        log_error(str(e))
    except Exception as e:
        print('Error loading CSV')
        log_error(str(e))

def check_table_exists(table_name, conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# === Step 2: Schema Inspection & Dynamic Creation ===
def create_table(csv_path, table_name, conn):
    df = pd.read_csv(csv_path, nrows=100)
    map = {"object": "TEXT", "int64": "INTEGER", "float64": "REAL"}
    columns = []
    for col, dtype in zip(df.columns, df.dtypes):
        if col.lower() == "id":
            columns.append(f"{col} INTEGER PRIMARY KEY AUTOINCREMENT")
        else:
            sql_type = map.get(str(dtype), 'TEXT')
            columns.append(f"{col} {sql_type}")
    create_stmt = f"CREATE TABLE {table_name} ({', '.join(columns)});"
    try:
        conn.execute(create_stmt)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Table '{table_name}' created and data inserted.")
    except Exception as e:
        log_error(str(e))
        print("Schema creation failed.")

def check_table_exists(table_name, conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def list_tables(conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor:
        print('-', row[0])

def run_query(conn):
    prompt = input("Enter your SQL query: ")
    try:
        if prompt.lower().startswith("select"):
            df = pd.read_sql_query(prompt, conn)
            print(df)
        else:
            cursor = conn.cursor()
            cursor.execute(prompt)
            conn.commit()
            print("Query executed successfully.")
    except Exception as e:
        print("Query failed.")
        log_error(str(e))

def use_ai_for_generation(user_query, schema):
    prompt = f'''
    You are an AI assistant tasked with converting user queries into SQL statements. The database uses SQLite and contains the following tables:
    {schema}
    User Query: "{user_query}"
    Your task is to:
    1. Generate a SQL query that accurately answers the user's question.
    2. Ensure the SQL is compatible with SQLite syntax.
    3. Provide a short comment explaining what the query does.
    Output Format:
    - SQL Query
    - Explanation
    '''
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    store=True,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    content = completion.choices[0].message.content
    sql_match = re.search(r"```sql\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
    sql_query = sql_match.group(1).strip() if sql_match else None


    # Extract everything after 'Explanation:' (optional whitespace after it)
    explanation_match = re.search(r"Explanation:\s*(.*)", content, re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else None
    print(sql_query)
    print(explanation)
    return sql_query, explanation

def handle_schema_conflict(csv_path, table_name, conn):
    if check_table_exists(table_name, conn):
        print(f"Conflict: Table '{table_name}' already exists.")
        action = input("Type 'overwrite', 'rename', or 'skip': ").strip().lower()
        if action == 'overwrite':
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            create_table(csv_path, table_name, conn)

        elif action == 'skip':
            print("Skipping.")

        elif action == 'rename':
            new_name = input("Enter new table name: ")
            create_table(csv_path, new_name, conn)

        else:
            print("Invalid action.")
    else:
        create_table(csv_path, table_name, conn)

def main():
    conn = connect_db()
    while True:
        print("\nOptions: load_csv|list_tables|run_query| ai_sql_chat|exit")
        action = input("Select option: ").strip().lower()

        if action == 'load_csv':
            path = input("CSV file path: ")
            table = input("Table name: ")
            handle_schema_conflict(path, table, conn)


        elif action == 'run_query':
            run_query(conn)

        elif action == 'list_tables':
            list_tables(conn)

        elif action == 'ai_sql_chat':
            schema = "\n".join(row[0] for row in conn.execute("SELECT sql FROM sqlite_master WHERE type='table'"))
            user_q = input("Ask a question: ")
            query, explanation = use_ai_for_generation(user_q, schema)
            print("\nGenerated SQL, its Answer and Explanation:\n")
            print("\nSQL:", query)

            try:
                if query.lower().startswith("select"):
                    df = pd.read_sql_query(query, conn)
                    print(df)
                else:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    conn.commit()
                    print("Query executed successfully.")
                print("\nExplanation:", explanation)

            except Exception as e:
                print("Query failed.")
                log_error(str(e))

        elif action == 'exit':
            break
        else:
            print("Unknown command.")

    conn.close()

if __name__ == "__main__":
    main()