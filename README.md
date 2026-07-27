# Personal Expense Tracker CLI

A dependency-free Python project for tracking personal expenses locally. It uses SQLite for persistent storage and provides a complete command-line interface—no website, AI, external API, or cloud account required.

## Features

- Add, list, update, and delete expenses
- Filter expenses by category or month
- View category and monthly spending summaries
- Export filtered records to CSV
- Store currency safely as integer cents
- Validate dates, amounts, categories, and descriptions
- Select a custom database file
- Load demonstration data
- Run entirely on your computer

## Requirements

- Python 3.9 or newer
- No third-party packages

## Quick start

```bash
python3 -m expense_tracker seed
python3 -m expense_tracker list
python3 -m expense_tracker summary --by category
```

The first command creates `expenses.db` and adds four demonstration records.

## Common commands

Add an expense:

```bash
python3 -m expense_tracker add 18.45 Food \
  --description "Lunch" \
  --date 2026-07-26
```

List expenses:

```bash
python3 -m expense_tracker list
python3 -m expense_tracker list --category Food
python3 -m expense_tracker list --month 2026-07
```

Update or delete:

```bash
python3 -m expense_tracker update 1 20.00 Food \
  --description "Lunch with tip" \
  --date 2026-07-26

python3 -m expense_tracker delete 1
```

Summaries:

```bash
python3 -m expense_tracker summary --by category --month 2026-07
python3 -m expense_tracker summary --by month
```

Export to CSV:

```bash
python3 -m expense_tracker export exports/july.csv --month 2026-07
```

Use a different database:

```bash
python3 -m expense_tracker --database work-expenses.db list
```

## Test

```bash
python3 -m unittest discover -v
python3 -m compileall -q expense_tracker
```

## Project structure

```text
expense_tracker/
  cli.py          Command parsing and terminal output
  database.py     SQLite schema and queries
  service.py      Validation and business rules
tests/
  test_expense_tracker.py
```

## Skills demonstrated

- Python modules and type hints
- Object-oriented design
- SQLite and parameterized SQL
- `argparse` command-line interfaces
- Decimal-safe currency handling
- CSV file operations
- Input validation and error handling
- Unit testing
- GitHub Actions

## License

MIT
