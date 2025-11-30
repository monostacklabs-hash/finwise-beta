"""
Export Service - TIER 1 Feature
Handles PDF reports, CSV exports, and tax document generation
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional, BinaryIO
from io import BytesIO, StringIO
import csv
import logging

from ..database.models import (
    Transaction,
    TransactionType,
    Goal,
    DebtLoan,
    Budget,
    User,
)
from ..services.health_calculator import HealthCalculator

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting financial data in various formats"""

    @staticmethod
    def export_transactions_csv(
        db: Session,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Export transactions to CSV format

        Args:
            db: Database session
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            CSV string
        """
        # Build query
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        transactions = query.order_by(Transaction.date.desc()).all()

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Date',
            'Type',
            'Category',
            'Description',
            'Amount',
            'Recurring',
            'Created At'
        ])

        # Data rows
        for txn in transactions:
            writer.writerow([
                txn.date.strftime('%Y-%m-%d'),
                txn.type.value,
                txn.category,
                txn.description,
                f"{txn.amount:.2f}",
                'Yes' if txn.recurring else 'No',
                txn.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return output.getvalue()

    @staticmethod
    def export_financial_report_pdf(
        db: Session,
        user_id: str,
        year: int,
        month: Optional[int] = None,
    ) -> bytes:
        """
        Generate a comprehensive financial report in PDF format

        Args:
            db: Database session
            user_id: User ID
            year: Year for the report
            month: Optional month (1-12) for monthly report

        Returns:
            PDF bytes
        """
        # This is a simplified version that returns HTML
        # In production, you'd use a library like ReportLab or WeasyPrint
        # to convert HTML to PDF

        html_report = ExportService._generate_financial_report_html(
            db, user_id, year, month
        )

        # For now, return HTML as bytes
        # TODO: Convert to PDF using reportlab or weasyprint
        return html_report.encode('utf-8')

    @staticmethod
    def export_tax_document(
        db: Session,
        user_id: str,
        tax_year: int,
    ) -> str:
        """
        Generate tax document with income and deductible expenses

        Args:
            db: Database session
            user_id: User ID
            tax_year: Tax year

        Returns:
            CSV string with tax-relevant transactions
        """
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59)

        # Get all transactions for the year
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).order_by(Transaction.date).all()

        # Get user info
        user = db.query(User).filter(User.id == user_id).first()

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Header section
        writer.writerow(['Tax Document Summary'])
        writer.writerow(['Tax Year:', tax_year])
        writer.writerow(['Name:', user.name if user else 'Unknown'])
        writer.writerow(['Email:', user.email if user else 'Unknown'])
        writer.writerow(['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])  # Blank row

        # Income summary
        income_transactions = [t for t in transactions if t.type == TransactionType.INCOME]
        total_income = sum(t.amount for t in income_transactions)

        writer.writerow(['INCOME SUMMARY'])
        writer.writerow(['Total Income:', f"${total_income:,.2f}"])
        writer.writerow(['Number of Income Transactions:', len(income_transactions)])
        writer.writerow([])

        # Income by category
        writer.writerow(['Income by Category'])
        writer.writerow(['Category', 'Amount'])
        income_by_category = {}
        for txn in income_transactions:
            cat = txn.category or 'uncategorized'
            income_by_category[cat] = income_by_category.get(cat, 0) + txn.amount

        for cat, amount in sorted(income_by_category.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([cat, f"${amount:,.2f}"])

        writer.writerow([])

        # Deductible expenses (you may want to customize this based on tax laws)
        deductible_categories = [
            'business',
            'healthcare',
            'education',
            'charity',
            'home_office',
        ]

        expense_transactions = [
            t for t in transactions
            if t.type == TransactionType.EXPENSE and t.category in deductible_categories
        ]

        writer.writerow(['POTENTIALLY DEDUCTIBLE EXPENSES'])
        writer.writerow(['Category', 'Date', 'Description', 'Amount'])

        for txn in expense_transactions:
            writer.writerow([
                txn.category,
                txn.date.strftime('%Y-%m-%d'),
                txn.description,
                f"${txn.amount:,.2f}"
            ])

        total_deductible = sum(t.amount for t in expense_transactions)
        writer.writerow([])
        writer.writerow(['Total Potentially Deductible:', f"${total_deductible:,.2f}"])
        writer.writerow([])
        writer.writerow(['DISCLAIMER: This is not tax advice. Consult a tax professional for accurate tax filing.'])

        return output.getvalue()

    @staticmethod
    def _generate_financial_report_html(
        db: Session,
        user_id: str,
        year: int,
        month: Optional[int] = None,
    ) -> str:
        """Generate HTML financial report"""

        # Date range
        if month:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            period_name = start_date.strftime('%B %Y')
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            period_name = str(year)

        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        # Get transactions
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()

        # Calculate metrics
        income_txns = [t for t in transactions if t.type == TransactionType.INCOME]
        expense_txns = [t for t in transactions if t.type == TransactionType.EXPENSE]

        total_income = sum(t.amount for t in income_txns)
        total_expenses = sum(t.amount for t in expense_txns)
        net_savings = total_income - total_expenses

        # Get financial health
        health_metrics = HealthCalculator.calculate_health(db, user_id)

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Financial Report - {period_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ font-size: 24px; font-weight: bold; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <h1>Financial Report</h1>
    <p><strong>Period:</strong> {period_name}</p>
    <p><strong>Name:</strong> {user.name if user else 'Unknown'}</p>
    <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Total Income: <span class="metric positive">${total_income:,.2f}</span></p>
        <p>Total Expenses: <span class="metric negative">${total_expenses:,.2f}</span></p>
        <p>Net Savings: <span class="metric {'positive' if net_savings >= 0 else 'negative'}">${net_savings:,.2f}</span></p>
        <p>Transactions: {len(transactions)}</p>
    </div>

    <div class="summary">
        <h2>Financial Health</h2>
        <p>Health Score: <span class="metric">{int(health_metrics['health_score'])}/100</span></p>
        <p>Assessment: {health_metrics['health_category']}</p>
        <p>Savings Rate: {health_metrics['savings_rate']:.1f}%</p>
    </div>

    <h2>Transaction History</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
"""

        for txn in sorted(transactions, key=lambda x: x.date, reverse=True):
            html += f"""
            <tr>
                <td>{txn.date.strftime('%Y-%m-%d')}</td>
                <td>{txn.type.value}</td>
                <td>{txn.category}</td>
                <td>{txn.description}</td>
                <td>${txn.amount:,.2f}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""

        return html
