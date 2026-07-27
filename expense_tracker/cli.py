"""Command-line interface for the Personal Expense Tracker."""

import argparse
import csv
import sys
from pathlib import Path

from .database import ExpenseDatabase
from .service import ExpenseService, parse_month


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def table(headers, rows) -> str:
    rows = [[str(cell) for cell in row] for row in rows]
    widths = [
        max(len(str(header)), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    line = "-+-".join("-" * width for width in widths)
    output = [
        " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers)),
        line,
    ]
    output.extend(
        " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in rows
    )
    return "\n".join(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="Track personal expenses locally with Python and SQLite.",
    )
    parser.add_argument(
        "--database", default="expenses.db", help="SQLite database path"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Add an expense")
    add.add_argument("amount", help="Expense amount, for example 12.50")
    add.add_argument("category", help="Category, for example Food")
    add.add_argument("-d", "--description", default="")
    add.add_argument("--date", help="Expense date in YYYY-MM-DD format")

    listing = commands.add_parser("list", help="List expenses")
    listing.add_argument("--category")
    listing.add_argument("--month", help="Filter by YYYY-MM")
    listing.add_argument("--limit", type=int)

    update = commands.add_parser("update", help="Update an expense")
    update.add_argument("id", type=int)
    update.add_argument("amount")
    update.add_argument("category")
    update.add_argument("-d", "--description", default="")
    update.add_argument("--date", required=True)

    delete = commands.add_parser("delete", help="Delete an expense")
    delete.add_argument("id", type=int)

    summary = commands.add_parser("summary", help="Show spending summaries")
    summary.add_argument(
        "--by", choices=["category", "month"], default="category"
    )
    summary.add_argument("--month", help="Filter category summary by YYYY-MM")

    export = commands.add_parser("export", help="Export expenses to CSV")
    export.add_argument("output", help="Destination CSV path")
    export.add_argument("--month", help="Filter by YYYY-MM")

    commands.add_parser("seed", help="Add demonstration expenses")
    return parser


def print_expenses(rows) -> None:
    if not rows:
        print("No expenses found.")
        return
    print(
        table(
            ["ID", "Date", "Category", "Description", "Amount"],
            [
                [
                    row["id"],
                    row["expense_date"],
                    row["category"],
                    row["description"] or "-",
                    money(row["amount_cents"]),
                ]
                for row in rows
            ],
        )
    )
    print(f"\nTotal: {money(sum(row['amount_cents'] for row in rows))}")


def run(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with ExpenseDatabase(args.database) as database:
            service = ExpenseService(database)
            if args.command == "add":
                expense_id = service.add(
                    args.amount, args.category, args.description, args.date
                )
                print(f"Added expense #{expense_id}.")
            elif args.command == "list":
                print_expenses(
                    database.list(args.category, parse_month(args.month), args.limit)
                )
            elif args.command == "update":
                changed = service.update(
                    args.id,
                    args.amount,
                    args.category,
                    args.description,
                    args.date,
                )
                print(f"Updated expense #{args.id}." if changed else "Expense not found.")
                return 0 if changed else 1
            elif args.command == "delete":
                deleted = database.delete(args.id)
                print(f"Deleted expense #{args.id}." if deleted else "Expense not found.")
                return 0 if deleted else 1
            elif args.command == "summary":
                if args.by == "category":
                    rows = database.category_summary(parse_month(args.month))
                    print(
                        table(
                            ["Category", "Entries", "Total"],
                            [
                                [row["category"], row["count"], money(row["total_cents"])]
                                for row in rows
                            ],
                        )
                    )
                else:
                    rows = database.monthly_summary()
                    print(
                        table(
                            ["Month", "Entries", "Total"],
                            [
                                [row["month"], row["count"], money(row["total_cents"])]
                                for row in rows
                            ],
                        )
                    )
            elif args.command == "export":
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                rows = database.list(month=parse_month(args.month))
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(
                        ["id", "date", "category", "description", "amount"]
                    )
                    writer.writerows(
                        [
                            row["id"],
                            row["expense_date"],
                            row["category"],
                            row["description"],
                            f"{row['amount_cents'] / 100:.2f}",
                        ]
                        for row in rows
                    )
                print(f"Exported {len(rows)} expenses to {output}.")
            elif args.command == "seed":
                examples = [
                    ("18.45", "Food", "Lunch", "2026-07-20"),
                    ("72.00", "Transport", "Monthly train pass", "2026-07-19"),
                    ("9.99", "Subscriptions", "Music", "2026-07-18"),
                    ("42.30", "Groceries", "Weekly groceries", "2026-07-17"),
                ]
                for example in examples:
                    service.add(*example)
                print(f"Added {len(examples)} demonstration expenses.")
        return 0
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
