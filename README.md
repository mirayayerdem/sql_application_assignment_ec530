# Author: Miray Ayerdem

# SQL Application Assistant
A simple, interactive Python-based assistant that lets you:

- Load CSV files into a SQLite database 
- Explore data using natural language via OpenAI 
- Run SQL queries through a CLI 

---
## Features

- CSV → SQLite table creation
- Automatic schema inference
- AI-powered SQL generation from natural language
- Basic query runner
- Error logging

---

## Requirements

- Python 3.8+
- `pandas`
- `openai`
- (Optional) `.env` file with your OpenAI API key

---

## Setup

```bash
# Install dependencies
pip install pandas openai

# (Optional) Create a .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

---

## Run the App

```bash
python chat_main.py
```

Example options:
```
Options: load_csv | list_tables | run_query | ai_sql_chat | exit
```

---

##  Running Tests (with GitHub Actions support)

```bash
python -m unittest test_chat_main.py
```

---

##  Sample CSV Format

```csv
id,name,age,salary
1,Alice,30,60000
2,Bob,40,70000
```

---

##  Notes

- Your OpenAI API key must be set as an environment variable or `.env` file
- All errors are logged to `error_logs.txt`
