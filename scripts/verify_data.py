# =============================================================================
# verify_data.py — Sanity checks after scraping and DB insert
# Run this AFTER db_insert.py to confirm everything looks good.
# =============================================================================

import mysql.connector
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Same connection helper as in db_insert.py."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "real_estate_mumbai"),
        charset="utf8mb4"
    )

def run_query(conn, sql: str) -> pd.DataFrame:
    """Runs a SQL query and returns the result as a Pandas DataFrame."""
    return pd.read_sql(sql, conn)

def main():
    conn = get_connection()
    
    print("\n" + "="*60)
    print("DATA VERIFICATION REPORT")
    print("="*60)
    
    # -------------------------------------------------------------------------
    # CHECK (a): Total row count in database
    # -------------------------------------------------------------------------
    df_total = run_query(conn, "SELECT COUNT(*) AS total_rows FROM raw_listings;")
    total_rows = df_total["total_rows"].iloc[0]
    
    print(f"\n[A] Total rows in raw_listings: {total_rows}")
    
    if total_rows < 3000:
        print(f"  ⚠️  WARNING: Only {total_rows} rows — target is 3,000+")
        print("      Consider: increasing MAX_PAGES_PER_CITY or scraping more cities")
    else:
        print(f"  ✓ Good! You've met the 3,000 row minimum.")
    
    # -------------------------------------------------------------------------
    # CHECK (b): Row count per city
    # -------------------------------------------------------------------------
    df_cities = run_query(conn, """
        SELECT 
            city,
            COUNT(*) AS listing_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct_of_total
        FROM raw_listings
        GROUP BY city
        ORDER BY listing_count DESC;
    """)
    
    print("\n[B] Listings per city:")
    print(df_cities.to_string(index=False))
    
    # -------------------------------------------------------------------------
    # CHECK (c): First 5 rows (sanity check — are fields populated?)
    # -------------------------------------------------------------------------
    df_sample = run_query(conn, """
        SELECT 
            id, city, locality, bhk_raw, price_raw, area_raw, listing_url
        FROM raw_listings
        LIMIT 5;
    """)
    
    print("\n[C] First 5 rows (selected columns):")
    # Set display options so columns don't get truncated
    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.width", 200)
    print(df_sample.to_string(index=False))
    
    # -------------------------------------------------------------------------
    # CHECK (d): Empty / NULL column analysis
    # -------------------------------------------------------------------------
    print("\n[D] NULL / empty field counts (fields with high NULL % need attention):")
    
    columns_to_check = [
        "title", "locality", "city", "bhk_raw", "price_raw",
        "price_per_sqft_raw", "area_raw", "floor_raw",
        "furnishing_raw", "society_raw", "listing_url"
    ]
    
    null_results = []
    for col in columns_to_check:
        df_null = run_query(conn, f"""
            SELECT 
                '{col}' AS column_name,
                COUNT(*) AS total,
                SUM(CASE WHEN {col} IS NULL OR {col} = '' THEN 1 ELSE 0 END) AS null_count,
                ROUND(
                    SUM(CASE WHEN {col} IS NULL OR {col} = '' THEN 1 ELSE 0 END) 
                    * 100.0 / COUNT(*), 1
                ) AS null_pct
            FROM raw_listings;
        """)
        null_results.append(df_null)
    
    df_nulls = pd.concat(null_results, ignore_index=True)
    print(df_nulls.to_string(index=False))
    
    # Flag columns with >50% nulls
    high_null = df_nulls[df_nulls["null_pct"] > 50]
    if not high_null.empty:
        print("\n  ⚠️  Columns with >50% NULL values:")
        for _, row in high_null.iterrows():
            print(f"     - {row['column_name']}: {row['null_pct']}% empty")
        print("      These fields likely need a selector update in the scraper.")
    
    # -------------------------------------------------------------------------
    # CHECK (e): Sample of listing URLs (confirm they're real URLs)
    # -------------------------------------------------------------------------
    df_urls = run_query(conn, """
        SELECT listing_url FROM raw_listings LIMIT 3;
    """)
    
    print("\n[E] Sample listing URLs (verify these are real property pages):")
    for _, row in df_urls.iterrows():
        print(f"    {row['listing_url'][:100]}")
    
    conn.close()
    
    # -------------------------------------------------------------------------
    # CHECK (f): CSV backup file
    # -------------------------------------------------------------------------
    csv_path = Path("data/raw_listings_backup.csv")
    if csv_path.exists():
        df_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
        print(f"\n[F] CSV backup: {csv_path} — {len(df_csv)} rows, {len(df_csv.columns)} columns")
        print(f"    Columns: {list(df_csv.columns)}")
    else:
        print(f"\n[F] ⚠️  CSV backup not found at {csv_path}")
    
    print("\n" + "="*60)
    print("Verification complete.")
    print("="*60)

if __name__ == "__main__":
    main()