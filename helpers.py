from database import get_db_connection

CATEGORIES = ['Food', 'Transport', 'Accommodation',
              'Books and Stationery', 'Healthcare',
              'Entertainment', 'Communication', 'Other']

def get_financial_summary(user_id):
    conn = get_db_connection()
    income_row = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="income"',
        (user_id,)).fetchone()
    expense_row = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="expense"',
        (user_id,)).fetchone()
    total_income  = income_row[0] or 0
    total_expense = expense_row[0] or 0
    balance       = total_income - total_expense
    cat_rows = conn.execute(
        'SELECT category, SUM(amount) as total FROM transactions WHERE user_id=? AND type="expense" GROUP BY category',
        (user_id,)).fetchall()
    category_totals = {row['category']: row['total'] for row in cat_rows}
    conn.close()
    return {
        'total_income':    round(total_income, 2),
        'total_expense':   round(total_expense, 2),
        'balance':         round(balance, 2),
        'category_totals': category_totals
    }

def prepare_chart_data(user_id):
    summary = get_financial_summary(user_id)
    cat_totals = summary['category_totals']
    labels  = list(cat_totals.keys())
    amounts = list(cat_totals.values())
    return labels, amounts