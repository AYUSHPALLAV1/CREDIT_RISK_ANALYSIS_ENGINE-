import os
from dotenv import load_dotenv
from src.db import ensure_database, get_conn, create_tables
from src.etl import load_csv_into_mysql
from src.risk import score_all
from src.finance import compute_all


def run(csv_path=os.path.join("data", "raw", "application_record.csv")):
    db_name = ensure_database()
    conn = get_conn(db_name)
    create_tables(conn)
    conn.close()

    load_csv_into_mysql(csv_path)
    score_all()
    compute_all()
    print("Pipeline complete: ETL, risk scoring, finance metrics.")


if __name__ == "__main__":
    load_dotenv()
    run()

