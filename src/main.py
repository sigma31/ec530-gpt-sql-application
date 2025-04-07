import sqlite3
import pandas as pd
import os

def connect_db(db_name=":memory:"):
    """Connect to SQLite database (default: in-memory)."""
    return sqlite3.connect(db_name)

def infer_sql_type(dtype):
    """Map pandas dtype to SQLite type."""
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
    """Load CSV file into a SQLite table with inferred schema."""
    try:
        df = pd.read_csv(csv_file)

        columns = []
        for col in df.columns:
            sql_type = infer_sql_type(df[col].dtype)
            columns.append(f'"{col}" {sql_type}')
        schema = ", ".join(columns)
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({schema});'
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        conn.execute(create_stmt)
        conn.commit()

        # Insert data
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Loaded {csv_file} into table '{table_name}' with inferred schema.")
    except Exception as e:
        print(f"Error loading CSV: {e}")

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

        elif cmd == "exit":
            print("Exiting.")
            conn.close()
            break

        else:
            print("Invalid command. Try again.")

if __name__ == "__main__":
    main()
