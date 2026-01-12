import os
import pandas as pd
import pymysql
import numpy as np
from src.db import create_tables, ensure_database, get_conn


def load_csv_into_mysql(csv_path=os.path.join("data", "raw", "application_record.csv")):
    db_name = ensure_database()
    conn = get_conn(db_name)
    create_tables(conn)
    cur = conn.cursor()

    df = pd.read_csv(csv_path)

    cols = [
        "ID",
        "CODE_GENDER",
        "FLAG_OWN_CAR",
        "FLAG_OWN_REALTY",
        "CNT_CHILDREN",
        "AMT_INCOME_TOTAL",
        "NAME_INCOME_TYPE",
        "NAME_EDUCATION_TYPE",
        "NAME_FAMILY_STATUS",
        "NAME_HOUSING_TYPE",
        "DAYS_BIRTH",
        "DAYS_EMPLOYED",
        "FLAG_MOBIL",
        "FLAG_WORK_PHONE",
        "FLAG_PHONE",
        "FLAG_EMAIL",
        "OCCUPATION_TYPE",
        "CNT_FAM_MEMBERS",
    ]

    df = df[cols]
    
    # Replace NaN with None for MySQL compatibility
    df = df.replace({np.nan: None})

    insert_sql = (
        "INSERT INTO applications (id, code_gender, flag_own_car, flag_own_realty, cnt_children, "
        "amt_income_total, name_income_type, name_education_type, name_family_status, name_housing_type, "
        "days_birth, days_employed, flag_mobil, flag_work_phone, flag_phone, flag_email, occupation_type, cnt_fam_members) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE code_gender=VALUES(code_gender), flag_own_car=VALUES(flag_own_car), "
        "flag_own_realty=VALUES(flag_own_realty), cnt_children=VALUES(cnt_children), amt_income_total=VALUES(amt_income_total), "
        "name_income_type=VALUES(name_income_type), name_education_type=VALUES(name_education_type), name_family_status=VALUES(name_family_status), "
        "name_housing_type=VALUES(name_housing_type), days_birth=VALUES(days_birth), days_employed=VALUES(days_employed), "
        "flag_mobil=VALUES(flag_mobil), flag_work_phone=VALUES(flag_work_phone), flag_phone=VALUES(flag_phone), flag_email=VALUES(flag_email), "
        "occupation_type=VALUES(occupation_type), cnt_fam_members=VALUES(cnt_fam_members)"
    )

    data = [tuple(row) for row in df.values]

    try:
        batch_size = 5000
        total_records = len(data)
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            cur.executemany(insert_sql, batch)
            conn.commit()
            print(f"ETL: Loaded {min(i + batch_size, total_records)} / {total_records} records...")
            
    except pymysql.Error as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

