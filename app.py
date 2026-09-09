from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from helpers import get_financial_summary, prepare_chart_data, CATEGORIES
from datetime import datetime
import json
import functools

app = Flask(__name__,
static_folder='static')
app.secret_key = 'stephanie_budget_secret_2025'

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        confirm  = request.form['confirm']
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT id FROM users WHERE username=? OR email=?',
            (username, email)).fetchone()
        if existing:
            conn.close()
            flash('Username or email already taken.', 'error')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        today  = datetime.today().strftime('%Y-%m-%d')
        conn.execute(
            'INSERT INTO users (username,email,password_hash,date_registered) VALUES (?,?,?,?)',
            (username, email, hashed, today))
        conn.commit()
        conn.close()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username=?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    summary = get_financial_summary(session['user_id'])
    labels, amounts = prepare_chart_data(session['user_id'])
    return render_template('dashboard.html',
        total_income  = summary['total_income'],
        total_expense = summary['total_expense'],
        balance       = summary['balance'],
        chart_labels  = json.dumps(labels),
        chart_amounts = json.dumps(amounts))

@app.route('/add-transaction', methods=['GET','POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        t_type      = request.form['type']
        amount      = request.form['amount']
        category    = request.form['category']
        description = request.form.get('description', '')
        date        = request.form['date']
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return redirect(url_for('add_transaction'))
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO transactions (user_id,type,amount,category,description,date) VALUES (?,?,?,?,?,?)',
            (session['user_id'], t_type, amount, category, description, date))
        conn.commit()
        conn.close()
        flash('Transaction recorded successfully.', 'success')
        return redirect(url_for('transactions'))
    return render_template('add_transaction.html', categories=CATEGORIES)

@app.route('/transactions')
@login_required
def transactions():
    conn = get_db_connection()
    records = conn.execute(
        'SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC',
        (session['user_id'],)).fetchall()
    conn.close()
    return render_template('transactions.html', records=records)

@app.route('/delete-transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM transactions WHERE id=?',(id,)).fetchone()
    if record and record['user_id'] == session['user_id']:
        conn.execute('DELETE FROM transactions WHERE id=?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('transactions'))

@app.route('/reports')
@login_required
def reports():
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT strftime('%Y-%m', date) as month,
                  SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                  SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
           FROM transactions WHERE user_id=?
           GROUP BY month ORDER BY month''',
        (session['user_id'],)).fetchall()
    conn.close()
    months   = [r['month']   for r in rows]
    incomes  = [r['income']  for r in rows]
    expenses = [r['expense'] for r in rows]
    labels, amounts = prepare_chart_data(session['user_id'])
    return render_template('reports.html',
        months   = json.dumps(months),
        incomes  = json.dumps(incomes),
        expenses = json.dumps(expenses),
        cat_labels  = json.dumps(labels),
        cat_amounts = json.dumps(amounts))

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id=?',
                        (session['user_id'],)).fetchone()
    if request.method == 'POST':
        new_email  = request.form['email'].strip()
        current_pw = request.form['current_password']
        new_pw     = request.form['new_password']
        if not check_password_hash(user['password_hash'], current_pw):
            flash('Current password is incorrect.', 'error')
            conn.close()
            return redirect(url_for('profile'))
        new_hash = generate_password_hash(new_pw) if new_pw else user['password_hash']
        conn.execute('UPDATE users SET email=?, password_hash=? WHERE id=?',
                     (new_email, new_hash, session['user_id']))
        conn.commit()
        conn.close()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    conn.close()
    return render_template('profile.html', user=user)


init_db()
if __name__ == '__main__':

    app.run(debug=True)