import sqlite3
import pandas as pd
import os
from openai import OpenAI

def load_openai_key(filepath="key.txt"):
    """Load OpenAI API key from a file in the current working directory."""
    filepath = os.path.join(os.getcwd(), filepath)
    try:
        with open(filepath, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Could not find {filepath}. Please create the file with your OpenAI API key.")
        return None

# Create the OpenAI client using the loaded key
api_key = load_openai_key()
if not api_key:
    exit(1)

client = OpenAI(api_key=api_key)

def connect_db(db_name=":memory:"):
    """Connect to SQLite database (default: in-memory)."""
    return sqlite3.connect(db_name)

def table_exists(conn, table_name):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    return cursor.fetchone() is not None

def get_table_schema(conn, table_name):
    cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
    return [(row[1], row[2]) for row in cursor.fetchall()]  # [(name, type), ...]

def infer_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "TEXT"

def load_csv_to_table(conn, csv_file, table_name):
    """Load CSV into SQLite table with schema conflict handling."""
    try:
        df = pd.read_csv(csv_file)
        inferred_schema = [(col, infer_sql_type(df[col].dtype)) for col in df.columns]

        if table_exists(conn, table_name):
            existing_schema = get_table_schema(conn, table_name)

            # Compare schemas
            if existing_schema != inferred_schema:
                print(f"Schema conflict detected for table '{table_name}'.")
                print("Options: [o]verwrite | [r]ename table | [s]kip")
                action = input("Choose an action: ").strip().lower()

                if action == "o":
                    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                elif action == "r":
                    new_table_name = input("Enter new table name: ").strip()
                    return load_csv_to_table(conn, csv_file, new_table_name)
                elif action == "s":
                    print("Skipping table creation.")
                    return
                else:
                    print("Invalid action. Skipping.")
                    return

        column_defs = [f'"{col}" {sql_type}' for col, sql_type in inferred_schema]
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(column_defs)});'
        conn.execute(create_stmt)
        conn.commit()

        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Loaded {csv_file} into table '{table_name}'")

    except Exception as e:
        print(f"Error loading CSV: {e}")
        log_error(f"[load_csv_to_table] {e}")

def interactive_sql_shell(conn):
    """Interactive SQL shell for executing queries."""
    while True:
        query = input("sqlite> ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Exiting SQL shell...")
            break
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(row)
        except Exception as e:
            print(f"SQL Error: {e}")

def log_error(message):
    with open("error_log.txt", "a") as f:
        f.write(message + "\n")
        
def get_all_tables_and_schema(conn):
    schema = ""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        schema += f"\nTable: {table}\n"
        schema += f"Columns:\n"
        for col, dtype in get_table_schema(conn, table):
            schema += f"  - {col} ({dtype})\n"
    return schema
        
def ask_ai_for_sql(user_request, table_schema):
    prompt = f"""
You are an expert SQL assistant. The database uses SQLite. Given the following SQLite table schema:

{table_schema}

Generate an SQL query that fulfills this user request:
\"\"\"{user_request}\"\"\"

Only return the SQL query.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        log_error(f"[ask_ai_for_sql] {e}")
        print(f"OpenAI Error: {e}")
        return None


def main():
    """Main CLI loop."""
    db_name = input("Enter database name (or press Enter for in-memory): ").strip() or ":memory:"
    conn = connect_db(db_name)

    while True:
        print("\nCommands: [load] Load CSV | [sql] Run SQL | [exit] Quit")
        cmd = input("Command: ").strip().lower()

        if cmd == "load":
            csv_file = input("Enter CSV file path: ").strip()
            if os.path.exists(csv_file):
                table_name = input("Enter table name: ").strip()
                load_csv_to_table(conn, csv_file, table_name)
            else:
                print("File not found.")
        
        elif cmd == "sql":
            interactive_sql_shell(conn)
            
        elif cmd == "chat":
            user_request = input("Ask something about your data: ").strip()
            schema = get_all_tables_and_schema(conn)
            sql_query = ask_ai_for_sql(user_request, schema)
            
            if sql_query:
                print(f"\nGenerated SQL:\n{sql_query}\n")
                confirm = input("Run this query? [y/N]: ").strip().lower()
                if confirm == "y":
                    try:
                        cursor = conn.execute(sql_query)
                        rows = cursor.fetchall()
                        if rows:
                            for row in rows:
                                print(row)
                        else:
                            print("Query executed. No rows returned.")
                    except Exception as e:
                        print(f"SQL Execution Error: {e}")
                        log_error(f"[SQL Execution] {e}\nQuery: {sql_query}")


        elif cmd == "exit":
            print("Exiting.")
            conn.close()
            break

        else:
            print("Invalid command. Try again.")

if __name__ == "__main__":
    main()
