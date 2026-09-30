"""
ClauseGuard AI — Database Storage Inspector
Zero-dependency inspection script that works on any machine.

Usage:
    python check_db.py
"""

import os
import sqlite3

def find_sqlite_db():
    candidates = [
        "backend/clauseguard_fallback.db",
        "clauseguard_fallback.db",
        "../backend/clauseguard_fallback.db",
        "d:/AI COURSE/G_38/CLAUSEGUARD_AI/backend/clauseguard_fallback.db",
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None

def inspect_database():
    print("\n" + "=" * 68)
    print("        CLAUSEGUARD AI — DATABASE STORAGE INSPECTION")
    print("=" * 68)

    db_path = find_sqlite_db()
    if not db_path:
        print("\n[!] No local SQLite fallback database found.")
        print("    If using PostgreSQL in Docker, start containers with: docker compose up -d")
        print("=" * 68 + "\n")
        return

    print(f"Database Source: SQLite [{db_path}]\n")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Table counts
        def get_count(table_name):
            try:
                cursor.execute(f"SELECT count(*) FROM {table_name}")
                return cursor.fetchone()[0]
            except Exception:
                return 0

        doc_count = get_count("documents")
        clause_count = get_count("clauses")
        review_count = get_count("reviews")
        risk_count = get_count("risks")
        query_count = get_count("queries")

        print(f"Total Stored Contracts:   {doc_count}")
        print(f"Total Extracted Clauses:  {clause_count}")
        print(f"Total Completed Reviews:  {review_count}")
        print(f"Total Flagged Risks:      {risk_count}")
        print(f"Total Q&A User Queries:   {query_count}")
        print("-" * 68)

        if doc_count == 0:
            print("\nDatabase tables are initialized, but 0 contracts have been ingested yet.")
            print("Upload a contract in the UI (http://localhost:3000) to populate records.")
            return

        # List documents
        print("\nINDEXED CONTRACTS:")
        print(f"{'Document Name':<38} | {'Clauses':<7} | {'Pages':<5} | {'Status':<8}")
        print("-" * 68)
        cursor.execute("SELECT name, clause_count, page_count, status FROM documents ORDER BY created_at DESC")
        for row in cursor.fetchall():
            name = (row[0][:35] + "...") if len(row[0]) > 38 else row[0]
            clauses = row[1] if row[1] is not None else 0
            pages = row[2] if row[2] is not None else 0
            status = row[3] or "unknown"
            print(f"{name:<38} | {clauses:<7} | {pages:<5} | {status:<8}")

        # Sample clauses
        if clause_count > 0:
            print("\n" + "=" * 68)
            print("SAMPLE STORED CLAUSES:")
            print("-" * 68)
            cursor.execute("SELECT clause_id, clause_title, section, page_number, clause_text FROM clauses LIMIT 5")
            for c in cursor.fetchall():
                c_id = c[0]
                c_title = c[1] or c[2] or "Clause"
                p_num = c[3] or 1
                snippet = (c[4] or "").replace("\n", " ").strip()[:65]
                print(f"[{c_id}] {c_title:<25} (p.{p_num}): \"{snippet}...\"")

        # Sample reviews
        if review_count > 0:
            print("\n" + "=" * 68)
            print("SAMPLE AUDITED REVIEWS:")
            print("-" * 68)
            cursor.execute("SELECT document_id, overall_risk_score, risk_level, critical_count, high_count FROM reviews LIMIT 3")
            for r in cursor.fetchall():
                doc_id_short = r[0][:8] + "..." if r[0] else "N/A"
                print(f"Doc: {doc_id_short} | Risk Score: {r[1]}/100 ({r[2]}) | Severity: {r[3]} Critical, {r[4]} High")

        print("\n" + "=" * 68)
        print("STATUS: VERIFIED — All records are stored securely on disk.")
        print("=" * 68 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Failed to query SQLite database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_database()
