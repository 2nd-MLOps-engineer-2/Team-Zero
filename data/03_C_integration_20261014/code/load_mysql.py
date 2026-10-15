"""MySQL 8.0 레이어별 적재: tz_bronze(인계 원본 그대로) → tz_silver(표준) → tz_gold(AI 데이터셋) + tz_meta(사전·실행기록).

실행: python code/load_mysql.py [--host 127.0.0.1 --port 3306 --user root --password ... | --socket ...]
      (비밀번호는 환경변수 MYSQL_PWD 로도 전달 가능)
전제: run_pipeline.py, build_model.py 를 먼저 실행해 04_output/ 와 03_model/ddl/ 이 있어야 한다.

재실행 일관성: Bronze/Silver/Gold/사전 테이블은 매번 DROP→CREATE→적재(같은 입력이면 같은 결과).
            m_exec_log 만 누적 보존한다.
"""
from __future__ import annotations
import argparse, datetime as dt, os, re

import pandas as pd
import pymysql

from common import ROOT, input_dirs, read_csv, sha256_file, input_manifest, input_version
from std_dictionary import TABLES, PIPELINE_VERSION
from build_model import BRONZE_SRC, SILVER_ORDER, DB

DDL = ROOT / "03_model" / "ddl"
OUT = ROOT / "04_output"
BATCH = 5000


def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")


def connect(a):
    kw = dict(user=a.user, password=a.password or os.environ.get("MYSQL_PWD", ""), charset="utf8mb4",
              autocommit=False, local_infile=False)
    if a.socket:
        kw["unix_socket"] = a.socket
    else:
        kw.update(host=a.host, port=a.port)
    return pymysql.connect(**kw)


def run_sql_file(cur, path):
    sql = path.read_text(encoding="utf-8")
    sql = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    for stmt in [s.strip() for s in re.split(r";\s*\n", sql) if s.strip()]:
        cur.execute(stmt)


def insert_df(cur, db, table, df: pd.DataFrame, empty_as_null=True):
    cols = list(df.columns)
    sql = f"INSERT INTO `{db}`.`{table}` ({','.join('`'+c+'`' for c in cols)}) VALUES ({','.join(['%s']*len(cols))})"
    data = df.to_numpy(dtype=object)
    for i in range(0, len(data), BATCH):
        chunk = data[i:i + BATCH]
        if empty_as_null:
            chunk = [[None if v == "" else v for v in row] for row in chunk]
        else:
            chunk = [list(r) for r in chunk]
        cur.executemany(sql, chunk)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", default="root"); ap.add_argument("--password"); ap.add_argument("--socket")
    ap.add_argument("--a-dir"); ap.add_argument("--b-dir")
    a = ap.parse_args()
    adir, bdir = input_dirs(a.a_dir, a.b_dir)
    iver = input_version(input_manifest(adir, bdir))
    run_id = "LOAD-" + dt.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + iver[-8:]
    con = connect(a)
    cur = con.cursor()
    log = []

    def L(step, layer, tbl, n, t0):
        log.append((run_id, step, tbl, layer, iver, n, t0, now(), "SUCCESS", PIPELINE_VERSION))

    for f in ("00_databases.sql", "01_bronze.sql", "02_silver.sql", "03_gold.sql", "04_meta.sql"):
        run_sql_file(cur, DDL / f)
    con.commit()

    # Bronze: 인계 CSV 를 문자열 그대로(빈값도 '' 그대로) 적재
    for tname, (team, rel) in BRONZE_SRC.items():
        t0 = now()
        path = (adir if team == "A" else bdir) / rel
        df = read_csv(path)
        df.insert(0, "ldng_row_no", range(1, len(df) + 1))
        df["ldng_file_path"] = f"{team}:{rel}"
        df["ldng_file_hash"] = "sha256:" + sha256_file(path)
        df["ldng_run_id"] = run_id
        insert_df(cur, "tz_bronze", tname, df, empty_as_null=False)
        con.commit()
        L("load_bronze", "BRONZE", tname, len(df), t0)
        print(f"bronze {tname:40s} {len(df):>8,}")

    # Silver (FK 순서) / Gold : 표준 CSV, 빈값 → NULL
    for layer, names, sub in (("SILVER", SILVER_ORDER, "silver"),
                              ("GOLD", [t for t in TABLES if TABLES[t]["layer"] == "GOLD"], "gold")):
        for n in names:
            t0 = now()
            df = read_csv(OUT / sub / f"{n}.csv")
            insert_df(cur, DB[layer], n, df)
            con.commit()
            L("load_" + sub, layer, n, len(df), t0)
            print(f"{sub:6s} {n:40s} {len(df):>8,}")

    # Meta: 표준 사전
    D = ROOT / "02_standard_dictionary"
    w = read_csv(D / "std_word.csv")[["word_nm", "word_kor_nm", "word_eng_nm", "word_cls_cd"]]
    insert_df(cur, "tz_meta", "m_std_word", w)
    d = read_csv(D / "std_domain.csv")
    insert_df(cur, "tz_meta", "m_std_dmn", d[["dmn_nm", "cls_word_nm", "data_type_nm", "data_len_txt", "allow_ptrn_txt", "dmn_desc_txt"]])
    t = read_csv(D / "std_term.csv")
    insert_df(cur, "tz_meta", "m_std_term", t[["tbl_nm", "col_nm", "term_kor_nm", "dmn_nm", "data_type_nm", "null_allow_yn",
                                                "pk_yn", "cd_grp_id", "layer_cd", "asis_src_txt"]])
    con.commit()
    L("load_meta", "META", "m_std_word/m_std_dmn/m_std_term", len(w) + len(d) + len(t), now())

    # 실행 기록: 파이프라인 기록 + 이번 적재 기록 (같은 run_id·step·tbl 은 갱신)
    pl = read_csv(OUT / "meta" / "m_exec_log.csv")
    rows = [tuple(r) for r in pl[["run_id", "step_nm", "tbl_nm", "layer_cd", "input_ver", "rcrd_cnt", "start_dttm",
                                   "end_dttm", "run_stts_cd", "pipln_ver"]].to_numpy()] + log
    cur.executemany("REPLACE INTO tz_meta.m_exec_log (run_id, step_nm, tbl_nm, layer_cd, input_ver, rcrd_cnt, start_dttm, "
                    "end_dttm, run_stts_cd, pipln_ver) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
    con.commit()
    print("load run:", run_id)
    con.close()


if __name__ == "__main__":
    main()
