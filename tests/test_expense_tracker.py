import csv
import tempfile
import unittest
from pathlib import Path

from expense_tracker.cli import run
from expense_tracker.database import ExpenseDatabase
from expense_tracker.service import (
    ExpenseService,
    clean_category,
    parse_amount,
    parse_date,
    parse_month,
)


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.database = ExpenseDatabase(":memory:")
        self.service = ExpenseService(self.database)

    def tearDown(self):
        self.database.close()

    def test_amount_is_stored_as_integer_cents(self):
        self.assertEqual(parse_amount("12.345"), 1235)
        self.assertEqual(parse_amount("0.01"), 1)

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_amount("-5")
        with self.assertRaises(ValueError):
            parse_date("07/26/2026")
        with self.assertRaises(ValueError):
            parse_month("2026-13")
        with self.assertRaises(ValueError):
            clean_category(" ")

    def test_add_and_filter_expenses(self):
        self.service.add("12.50", "food", "Lunch", "2026-07-20")
        self.service.add("20", "Transport", "Taxi", "2026-06-02")
        july = self.database.list(month="2026-07")
        self.assertEqual(len(july), 1)
        self.assertEqual(july[0]["category"], "Food")
        self.assertEqual(july[0]["amount_cents"], 1250)

    def test_update_and_delete_expense(self):
        expense_id = self.service.add("10", "Food", "Breakfast", "2026-07-20")
        changed = self.service.update(
            expense_id, "11.25", "Food", "Brunch", "2026-07-21"
        )
        self.assertTrue(changed)
        self.assertEqual(self.database.get(expense_id)["amount_cents"], 1125)
        self.assertTrue(self.database.delete(expense_id))
        self.assertIsNone(self.database.get(expense_id))

    def test_category_summary(self):
        self.service.add("10", "Food", "Lunch", "2026-07-20")
        self.service.add("5.50", "Food", "Coffee", "2026-07-21")
        self.service.add("20", "Travel", "Taxi", "2026-07-21")
        summary = self.database.category_summary("2026-07")
        self.assertEqual(summary[0]["category"], "Travel")
        food = next(row for row in summary if row["category"] == "Food")
        self.assertEqual(food["total_cents"], 1550)

    def test_csv_export(self):
        with tempfile.TemporaryDirectory() as temp:
            database_path = str(Path(temp) / "test.db")
            export_path = str(Path(temp) / "expenses.csv")
            self.assertEqual(
                run(
                    [
                        "--database",
                        database_path,
                        "add",
                        "8.25",
                        "Food",
                        "-d",
                        "Snack",
                        "--date",
                        "2026-07-26",
                    ]
                ),
                0,
            )
            self.assertEqual(
                run(["--database", database_path, "export", export_path]), 0
            )
            with open(export_path, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["amount"], "8.25")


if __name__ == "__main__":
    unittest.main()
