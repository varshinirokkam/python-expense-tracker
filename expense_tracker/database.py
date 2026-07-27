"""SQLite persistence for the expense tracker."""

import sqlite3
from pathlib import Path
from typing import Optional


class ExpenseDatabase:
    """Store and query expenses in a local SQLite database."""

    def __init__(self, database_path: str = "expenses.db") -> None:
        self.database_path = Path(database_path)
        self.connection = sqlite3.connect(str(self.database_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)"
        )
        self.connection.commit()

    def add(
        self, amount_cents: int, category: str, description: str, expense_date: str
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO expenses (amount_cents, category, description, expense_date)
            VALUES (?, ?, ?, ?)
            """,
            (amount_cents, category, description, expense_date),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list(
        self,
        category: Optional[str] = None,
        month: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        conditions = []
        parameters = []
        if category:
            conditions.append("LOWER(category) = LOWER(?)")
            parameters.append(category)
        if month:
            conditions.append("substr(expense_date, 1, 7) = ?")
            parameters.append(month)
        query = "SELECT * FROM expenses"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY expense_date DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)
        return self.connection.execute(query, parameters).fetchall()

    def get(self, expense_id: int):
        return self.connection.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()

    def update(
        self,
        expense_id: int,
        amount_cents: int,
        category: str,
        description: str,
        expense_date: str,
    ) -> bool:
        cursor = self.connection.execute(
            """
            UPDATE expenses
            SET amount_cents = ?, category = ?, description = ?, expense_date = ?
            WHERE id = ?
            """,
            (amount_cents, category, description, expense_date, expense_id),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def delete(self, expense_id: int) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM expenses WHERE id = ?", (expense_id,)
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def category_summary(self, month: Optional[str] = None):
        query = """
            SELECT category, COUNT(*) AS count, SUM(amount_cents) AS total_cents
            FROM expenses
        """
        parameters = []
        if month:
            query += " WHERE substr(expense_date, 1, 7) = ?"
            parameters.append(month)
        query += " GROUP BY category ORDER BY total_cents DESC"
        return self.connection.execute(query, parameters).fetchall()

    def monthly_summary(self):
        return self.connection.execute(
            """
            SELECT substr(expense_date, 1, 7) AS month,
                   COUNT(*) AS count,
                   SUM(amount_cents) AS total_cents
            FROM expenses
            GROUP BY month
            ORDER BY month DESC
            """
        ).fetchall()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
