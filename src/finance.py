from src.db import get_conn


def _finance_for_row(row):
    income = float(row["amt_income_total"] or 0.0)
    age = max(0, int(-int(row["days_birth"] or 0) // 365))
    dependents = int(row["cnt_children"] or 0)

    essentials = round(income * 0.5, 2)
    wants = round(income * 0.3, 2)
    savings = round(income * 0.2, 2)
    return income, essentials, wants, savings, age, dependents


def compute_all():
    conn = get_conn("credit_engine")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, amt_income_total, days_birth, cnt_children FROM applications"
    )
    rows = cur.fetchall()

    upsert_sql = (
        "INSERT INTO finance_metrics (id, monthly_income, essentials, wants, savings, age, dependents) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE monthly_income=VALUES(monthly_income), essentials=VALUES(essentials), "
        "wants=VALUES(wants), savings=VALUES(savings), age=VALUES(age), dependents=VALUES(dependents)"
    )

    data = []
    batch_size = 5000
    total_rows = len(rows)

    for i, r in enumerate(rows):
        income, essentials, wants, savings, age, deps = _finance_for_row(r)
        data.append((r["id"], income, essentials, wants, savings, age, deps))

        if len(data) >= batch_size:
            cur.executemany(upsert_sql, data)
            conn.commit()
            data = []
            print(f"Finance: Processed {i + 1} / {total_rows}...")

    if data:
        cur.executemany(upsert_sql, data)
        conn.commit()
        print(f"Finance: Processed {total_rows} / {total_rows}...")

    cur.close()
    conn.close()


