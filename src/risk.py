from src.db import get_conn


def _risk_score_row(row):
    amt_income = row["amt_income_total"] or 0
    children = int(row["cnt_children"] or 0)
    days_birth = int(row["days_birth"] or 0)
    days_employed = int(row["days_employed"] or 0)

    age = max(0, int(-days_birth // 365))
    employed_days_abs = abs(days_employed)

    score = 40
    if amt_income < 120000:
        score += 20
    elif amt_income < 240000:
        score += 10

    if children >= 2:
        score += 10
    elif children == 1:
        score += 5

    if age < 25 or age > 60:
        score += 10

    if employed_days_abs < 365:
        score += 10

    band = "low"
    if score > 60:
        band = "high"
    elif score > 45:
        band = "medium"

    return score, band, age


def score_all():
    conn = get_conn("credit_engine")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, amt_income_total, cnt_children, days_birth, days_employed FROM applications"
    )
    rows = cur.fetchall()

    upsert_sql = (
        "INSERT INTO risk_scores (id, risk_score, risk_band) VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE risk_score=VALUES(risk_score), risk_band=VALUES(risk_band)"
    )

    data = []
    batch_size = 5000
    total_rows = len(rows)

    for i, r in enumerate(rows):
        score, band, _ = _risk_score_row(r)
        data.append((r["id"], score, band))

        if len(data) >= batch_size:
            cur.executemany(upsert_sql, data)
            conn.commit()
            data = []
            print(f"Risk: Processed {i + 1} / {total_rows}...")

    if data:
        cur.executemany(upsert_sql, data)
        conn.commit()
        print(f"Risk: Processed {total_rows} / {total_rows}...")

    cur.close()
    conn.close()


