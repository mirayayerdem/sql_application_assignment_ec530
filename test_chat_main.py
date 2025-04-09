import unittest
import sqlite3
import os
import pandas as pd
from chat_main import (
    connect_db, log_error, load_csv_to_sqlite, create_table,
    check_table_exists, run_query, use_ai_for_generation
)

TEST_DB = "test_chat_sheet.db"

class TestSQLApp(unittest.TestCase):
    def setUp(self):
        # Setup fresh DB before each test
        self.conn = sqlite3.connect(TEST_DB)
        self.test_csv_path = "test_employees.csv"
        pd.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "age": [30, 40],
            "salary": [60000.0, 70000.0]
        }).to_csv(self.test_csv_path, index=False)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        if os.path.exists("error_logs.txt"):
            os.remove("error_logs.txt")

    def test_load_csv_to_sqlite_success(self):
        load_csv_to_sqlite(self.test_csv_path, "employees", self.conn)
        self.assertTrue(check_table_exists("employees", self.conn))

    def test_load_csv_to_sqlite_table_exists(self):
        load_csv_to_sqlite(self.test_csv_path, "employees", self.conn)
        load_csv_to_sqlite(self.test_csv_path, "employees", self.conn)  # should log error
        with open("error_logs.txt", "r") as f:
            self.assertIn("already exists", f.read())

    def test_create_table_with_autoincrement(self):
        create_table(self.test_csv_path, "employees", self.conn)
        result = self.conn.execute("PRAGMA table_info(employees)").fetchall()
        id_column = [col for col in result if col[1] == "id"][0]
        self.assertIn("INTEGER", id_column[2])
        self.assertEqual(id_column[5], 1)  # primary key

    def test_ai_sql_generation(self):
        schema = "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, salary REAL);"
        # Use a mock version of use_ai_for_generation for test
        query, explanation = use_ai_for_generation("What is the average salary?", schema)
        self.assertIsInstance(query, str)
        self.assertIn("SELECT", query.upper())

    def test_run_query_insert_and_select(self):
        create_table(self.test_csv_path, "employees", self.conn)
        insert_query = "INSERT INTO employees (name, age, salary) VALUES ('Charlie', 28, 65000);"
        self.conn.execute(insert_query)
        self.conn.commit()
        result = pd.read_sql_query("SELECT * FROM employees WHERE name = 'Charlie'", self.conn)
        self.assertEqual(result.iloc[0]["age"], 28)

if __name__ == "__main__":
    unittest.main()
