from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime

from src.db import ensure_database, get_conn, create_web_tables


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def init_db():
    db_name = ensure_database()
    conn = get_conn(db_name)
    create_web_tables(conn)
    conn.close()


def get_db():
    return get_conn("credit_engine")


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        age = request.form.get("age")
        monthly_income = request.form.get("monthly_income")
        employment_type = request.form.get("employment_type")

        if not email or not password:
            flash("Email and password are required.")
            return redirect(url_for("register"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        exists = cur.fetchone()
        if exists:
            flash("Email already registered.")
            cur.close()
            conn.close()
            return redirect(url_for("login"))

        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (email, password_hash, age, monthly_income, employment_type) VALUES (%s, %s, %s, %s, %s)",
            (email, pwd_hash, age or None, monthly_income or None, employment_type or None),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Registered successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row or not check_password_hash(row['password_hash'], password):
            flash("Invalid credentials.")
            return redirect(url_for("login"))
        session["user_id"] = row['id']
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def _month_filter():
    today = datetime.date.today()
    return today.year, today.month


def _compute_score(monthly_income, total_expenses, total_emi, age, employment_type):
    try:
        income = float(monthly_income or 0.0)
    except Exception:
        income = 0.0
    try:
        expenses = float(total_expenses or 0.0)
    except Exception:
        expenses = 0.0
    try:
        emi = float(total_emi or 0.0)
    except Exception:
        emi = 0.0

    if income <= 0:
        return 300, "high", 0.0, 0.0, 0.0, -expenses - emi

    savings = income - expenses - emi
    dti = (emi / income) if income > 0 else 0.0
    savings_rate = (savings / income) if income > 0 else 0.0

    score = 750
    # DTI adjustments
    if dti < 0.2:
        score += 50
    elif dti < 0.4:
        score += 0
    elif dti < 0.6:
        score -= 50
    else:
        score -= 100

    # Savings rate
    if savings_rate > 0.2:
        score += 25
    elif savings_rate < 0.05:
        score -= 25

    # Age
    age_val = int(age or 0)
    if 25 <= age_val <= 60:
        score += 10
    else:
        score -= 10

    # Employment type (simple bump for typical stable types)
    emp = (employment_type or "").lower()
    if emp in {"working", "commercial associate", "manager", "office work"}:
        score += 10

    score = max(300, min(850, score))
    if score >= 750:
        band = "low"
    elif score >= 650:
        band = "medium"
    else:
        band = "high"

    return score, band, dti, dti, savings_rate, savings


@app.route("/dashboard", methods=["GET"]) 
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT age, monthly_income, employment_type FROM users WHERE id=%s", (user_id,))
    urow = cur.fetchone()
    if urow:
        age = urow['age']
        monthly_income = urow['monthly_income']
        employment_type = urow['employment_type']
    else:
        age = None
        monthly_income = 0.0
        employment_type = ""

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM income WHERE user_id=%s AND MONTH(tx_date)=MONTH(CURDATE()) AND YEAR(tx_date)=YEAR(CURDATE())",
        (user_id,),
    )
    total_income = float(cur.fetchone()['total'] or 0.0)

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE user_id=%s AND MONTH(tx_date)=MONTH(CURDATE()) AND YEAR(tx_date)=YEAR(CURDATE())",
        (user_id,),
    )
    total_expenses = float(cur.fetchone()['total'] or 0.0)

    cur.execute("SELECT COALESCE(SUM(monthly_emi),0) as total FROM loans WHERE user_id=%s", (user_id,))
    total_emi = float(cur.fetchone()['total'] or 0.0)

    base_income = float(monthly_income or 0.0)
    shown_income = max(base_income, total_income)

    score, band, dti, emi_burden, savings_rate, savings = _compute_score(
        base_income, total_expenses, total_emi, age, employment_type
    )

    cur.execute(
        "INSERT INTO credit_score (user_id, score, risk_band, dti, emi_burden, savings_rate) VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE score=VALUES(score), risk_band=VALUES(risk_band), dti=VALUES(dti), emi_burden=VALUES(emi_burden), savings_rate=VALUES(savings_rate)",
        (user_id, int(score), band, dti, emi_burden, savings_rate),
    )
    conn.commit()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        age=age,
        monthly_income=base_income,
        employment_type=employment_type,
        total_income=shown_income,
        total_expenses=total_expenses,
        total_emi=total_emi,
        savings=savings,
        score=int(score),
        band=band,
        dti=round(dti, 3),
        savings_rate=round(savings_rate, 3),
    )


@app.route("/income", methods=["POST"]) 
def add_income():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    amount = request.form.get("amount")
    category = request.form.get("category") or "Other"
    tx_date = datetime.date.today()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income (user_id, amount, category, tx_date) VALUES (%s, %s, %s, %s)",
        (user_id, amount, category, tx_date),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/stocks", methods=["GET"])
def view_stocks():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM stocks WHERE user_id=%s ORDER BY ticker", (user_id,))
    stocks = cur.fetchall()

    total_investment = sum(s['quantity'] * s['avg_buy_price'] for s in stocks)
    current_value = sum(s['quantity'] * s['current_price'] for s in stocks)

    cur.close()
    conn.close()
    return render_template("stocks.html", stocks=stocks, total_investment=round(total_investment, 2), current_value=round(current_value, 2))


@app.route("/stocks/buy", methods=["POST"])
def buy_stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    ticker = request.form.get("ticker").upper().strip()
    qty = float(request.form.get("quantity"))
    price = float(request.form.get("price"))
    tx_date = datetime.date.today()

    conn = get_db()
    cur = conn.cursor()

    # Record Transaction
    cur.execute(
        "INSERT INTO stock_transactions (user_id, ticker, tx_type, quantity, price, tx_date) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, ticker, "BUY", qty, price, tx_date)
    )

    # Update Holdings
    cur.execute("SELECT * FROM stocks WHERE user_id=%s AND ticker=%s", (user_id, ticker))
    existing = cur.fetchone()

    if existing:
        new_qty = float(existing['quantity']) + qty
        total_cost = (float(existing['quantity']) * float(existing['avg_buy_price'])) + (qty * price)
        new_avg = total_cost / new_qty
        cur.execute(
            "UPDATE stocks SET quantity=%s, avg_buy_price=%s, current_price=%s WHERE id=%s",
            (new_qty, new_avg, price, existing['id'])
        )
    else:
        cur.execute(
            "INSERT INTO stocks (user_id, ticker, quantity, avg_buy_price, current_price) VALUES (%s, %s, %s, %s, %s)",
            (user_id, ticker, qty, price, price)
        )

    conn.commit()
    cur.close()
    conn.close()
    flash(f"Bought {qty} shares of {ticker} at ₹{price}")
    return redirect(url_for("view_stocks"))


@app.route("/stocks/sell", methods=["POST"])
def sell_stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    ticker = request.form.get("ticker")
    qty = float(request.form.get("quantity"))
    price = float(request.form.get("price"))
    tx_date = datetime.date.today()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM stocks WHERE user_id=%s AND ticker=%s", (user_id, ticker))
    existing = cur.fetchone()

    if not existing or float(existing['quantity']) < qty:
        flash("Insufficient quantity to sell.")
        return redirect(url_for("view_stocks"))

    # Record Transaction
    cur.execute(
        "INSERT INTO stock_transactions (user_id, ticker, tx_type, quantity, price, tx_date) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, ticker, "SELL", qty, price, tx_date)
    )

    new_qty = float(existing['quantity']) - qty
    if new_qty > 0:
        cur.execute("UPDATE stocks SET quantity=%s, current_price=%s WHERE id=%s", (new_qty, price, existing['id']))
    else:
        cur.execute("DELETE FROM stocks WHERE id=%s", (existing['id'],))

    conn.commit()
    cur.close()
    conn.close()
    flash(f"Sold {qty} shares of {ticker} at ₹{price}")
    return redirect(url_for("view_stocks"))


@app.route("/stocks/update", methods=["POST"])
def update_stock_price():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    ticker = request.form.get("ticker")
    new_price = request.form.get("new_price")

    if new_price:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE stocks SET current_price=%s WHERE user_id=%s AND ticker=%s", (new_price, user_id, ticker))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Updated price for {ticker}")

    return redirect(url_for("view_stocks"))


@app.route("/expense", methods=["POST"]) 
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    amount = request.form.get("amount")
    category = request.form.get("category") or "Other"
    tx_date = datetime.date.today()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (user_id, amount, category, tx_date) VALUES (%s, %s, %s, %s)",
        (user_id, amount, category, tx_date),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/loan", methods=["POST"]) 
def add_loan():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    principal = request.form.get("principal") or None
    monthly_emi = request.form.get("monthly_emi") or 0
    interest_rate = request.form.get("interest_rate") or None
    bank_name = request.form.get("bank_name")
    due_day = request.form.get("due_day")
    start_date = datetime.date.today()
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check if columns exist (handled by db migration, but safer to assume they do now)
    cur.execute(
        """
        INSERT INTO loans (user_id, principal, monthly_emi, interest_rate, start_date, bank_name, due_day) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, principal, monthly_emi, interest_rate, start_date, bank_name, due_day),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("view_accounts"))


@app.route("/accounts", methods=["GET"])
def view_accounts():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    # Fetch Banks
    cur.execute("SELECT * FROM bank_accounts WHERE user_id=%s ORDER BY bank_name", (user_id,))
    banks = cur.fetchall()

    # Fetch Credit Cards
    cur.execute("SELECT * FROM credit_cards WHERE user_id=%s ORDER BY bank_name", (user_id,))
    cards = cur.fetchall()

    # Fetch Loans (Liabilities)
    cur.execute("SELECT * FROM loans WHERE user_id=%s ORDER BY bank_name", (user_id,))
    loans = cur.fetchall()

    conn.close()
    
    total_liquidity = sum(float(b['balance']) for b in banks)
    total_debt = sum(float(c['outstanding_amount']) for c in cards) + sum(float(l['principal'] or 0) for l in loans)

    return render_template("accounts.html", banks=banks, cards=cards, loans=loans, total_liquidity=total_liquidity, total_debt=total_debt)


@app.route("/accounts/add_bank", methods=["POST"])
def add_bank():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    bank_name = request.form.get("bank_name")
    account_number = request.form.get("account_number")
    account_type = request.form.get("account_type")
    balance = request.form.get("balance")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bank_accounts (user_id, bank_name, account_number, account_type, balance) VALUES (%s, %s, %s, %s, %s)",
        (user_id, bank_name, account_number, account_type, balance)
    )
    conn.commit()
    conn.close()
    flash("Bank account added successfully.")
    return redirect(url_for("view_accounts"))


@app.route("/accounts/add_card", methods=["POST"])
def add_card():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    bank_name = request.form.get("bank_name")
    card_name = request.form.get("card_name")
    card_number = request.form.get("card_number")
    total_limit = request.form.get("total_limit")
    due_day = request.form.get("due_day")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO credit_cards (user_id, bank_name, card_name, card_number, total_limit, due_day) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, bank_name, card_name, card_number, total_limit, due_day)
    )
    conn.commit()
    conn.close()
    flash("Credit card added successfully.")
    return redirect(url_for("view_accounts"))


@app.route("/accounts/update_card", methods=["POST"])
def update_card():
    if "user_id" not in session:
        return redirect(url_for("login"))
    card_id = request.form.get("card_id")
    outstanding = request.form.get("outstanding_amount")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE credit_cards SET outstanding_amount=%s WHERE id=%s", (outstanding, card_id))
    conn.commit()
    conn.close()
    flash("Card updated.")
    return redirect(url_for("view_accounts"))


@app.route("/accounts/update_loan", methods=["POST"])
def update_loan():
    if "user_id" not in session:
        return redirect(url_for("login"))
    loan_id = request.form.get("loan_id")
    penalty = request.form.get("penalty_amount")
    overdue_days = request.form.get("overdue_days")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE loans SET penalty_amount=%s, overdue_days=%s WHERE id=%s", (penalty, overdue_days, loan_id))
    conn.commit()
    conn.close()
    flash("Loan updated.")
    return redirect(url_for("view_accounts"))



if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)

