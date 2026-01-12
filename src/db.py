import os
import pymysql


def get_conn(db_name=None):
    host = os.environ.get("DB_HOST", "127.0.0.1")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "ayush@1A")
    kwargs = {
        "host": host,
        "user": user,
        "password": password,
        "cursorclass": pymysql.cursors.DictCursor
    }
    if db_name:
        kwargs["database"] = db_name
    return pymysql.connect(**kwargs)


def ensure_database(db_name="credit_engine"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    cur.close()
    conn.close()
    return db_name


def create_tables(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id BIGINT PRIMARY KEY,
            code_gender VARCHAR(8),
            flag_own_car VARCHAR(2),
            flag_own_realty VARCHAR(2),
            cnt_children INT,
            amt_income_total DECIMAL(15,2),
            name_income_type VARCHAR(64),
            name_education_type VARCHAR(64),
            name_family_status VARCHAR(64),
            name_housing_type VARCHAR(64),
            days_birth INT,
            days_employed INT,
            flag_mobil TINYINT,
            flag_work_phone TINYINT,
            flag_phone TINYINT,
            flag_email TINYINT,
            occupation_type VARCHAR(64),
            cnt_fam_members DECIMAL(6,2)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_scores (
            id BIGINT PRIMARY KEY,
            risk_score INT,
            risk_band VARCHAR(16)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS finance_metrics (
            id BIGINT PRIMARY KEY,
            monthly_income DECIMAL(15,2),
            essentials DECIMAL(15,2),
            wants DECIMAL(15,2),
            savings DECIMAL(15,2),
            age INT,
            dependents INT
        )
        """
    )

    cur.close()
    conn.commit()

def create_web_tables(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            age INT,
            monthly_income DECIMAL(15,2),
            employment_type VARCHAR(64)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS income (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            category VARCHAR(64),
            tx_date DATE,
            INDEX (user_id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            category VARCHAR(64),
            tx_date DATE,
            INDEX (user_id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS loans (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            principal DECIMAL(15,2),
            monthly_emi DECIMAL(15,2) NOT NULL,
            interest_rate DECIMAL(7,3),
            start_date DATE,
            INDEX (user_id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_score (
            user_id BIGINT PRIMARY KEY,
            score INT,
            risk_band VARCHAR(16),
            dti DECIMAL(10,4),
            emi_burden DECIMAL(10,4),
            savings_rate DECIMAL(10,4),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            ticker VARCHAR(20) NOT NULL,
            quantity DECIMAL(15,4) DEFAULT 0,
            avg_buy_price DECIMAL(15,2) DEFAULT 0,
            current_price DECIMAL(15,2) DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            ticker VARCHAR(20) NOT NULL,
            tx_type VARCHAR(10) NOT NULL,
            quantity DECIMAL(15,4) NOT NULL,
            price DECIMAL(15,2) NOT NULL,
            tx_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # --- NEW TABLES FOR BANK ACCOUNTS AND LIABILITIES ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            bank_name VARCHAR(100) NOT NULL,
            account_number VARCHAR(50),
            account_type VARCHAR(50) DEFAULT 'Savings',
            balance DECIMAL(15,2) DEFAULT 0.00,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_cards (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            bank_name VARCHAR(100) NOT NULL,
            card_name VARCHAR(100),
            card_number VARCHAR(20),
            total_limit DECIMAL(15,2) DEFAULT 0.00,
            outstanding_amount DECIMAL(15,2) DEFAULT 0.00,
            due_day INT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # Attempt to upgrade loans table if it exists but lacks columns
    try:
        cur.execute("ALTER TABLE loans ADD COLUMN bank_name VARCHAR(100)")
    except pymysql.err.OperationalError:
        pass  # Column likely exists
    
    try:
        cur.execute("ALTER TABLE loans ADD COLUMN due_day INT")
    except pymysql.err.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE loans ADD COLUMN penalty_amount DECIMAL(15,2) DEFAULT 0.00")
    except pymysql.err.OperationalError:
        pass
        
    try:
        cur.execute("ALTER TABLE loans ADD COLUMN overdue_days INT DEFAULT 0")
    except pymysql.err.OperationalError:
        pass

    cur.close()
    conn.commit()




