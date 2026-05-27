import os
import logging
import datetime
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
from pathlib import Path

# Configure a professional logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Load database credentials securely
load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "real_estate_mumbai"),
            charset="utf8mb4"
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {e}")
        raise e

def insert_kaggle_listings(df):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO raw_listings (
        listing_url, title, locality, city, bhk_raw, 
        price_raw, price_per_sqft_raw, area_raw, 
        floor_raw, furnishing_raw, society_raw, scraped_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title);
    """
    
    inserted = 0
    dupes = 0
    errors = 0
    
    logger.info(f"Starting database migration of {len(df)} rows...")
    
    for idx, row in df.iterrows():
        try:
            # Create unique URL
            fake_url = f"https://www.magicbricks.com/property/kaggle_pro_id_{idx}"
            
           # --- UPDATED SCHEMA MAPPING ---
            # The 'title' column in this dataset is actually the building/society name
            society_raw = str(row['title']) if pd.notna(row['title']) else None
            
            # We will construct a clean title for our database using the actual data
            bhk_val = str(row['bedroom_num']) if pd.notna(row['bedroom_num']) else "Unknown"
            loc_val = str(row['locality']) if pd.notna(row['locality']) else "Unknown"
            title = f"{bhk_val} BHK in {loc_val}"
            
            # Map the rest normally
            price_raw = str(row['price']) if pd.notna(row['price']) else None
            area_raw = str(row['area']) if pd.notna(row['area']) else None
            price_per_sqft_raw = str(row['price_per_sqft']) if pd.notna(row['price_per_sqft']) else None
            furnishing_raw = str(row['furnished']) if pd.notna(row['furnished']) else None
            floor_raw = str(row['total_floors']) if pd.notna(row['total_floors']) else None
            city = str(row['city']) if pd.notna(row['city']) else "Mumbai"
            
            # Directly map the columns we previously ignored
            locality = loc_val if loc_val != "Unknown" else None
            bhk_raw = bhk_val if bhk_val != "Unknown" else None
            
            scraped_at = datetime.datetime.now()
            
            # Execute query
            cursor.execute(insert_query, (
                fake_url, title, locality, city, bhk_raw,
                price_raw, price_per_sqft_raw, area_raw,
                floor_raw, furnishing_raw, society_raw, scraped_at
            ))
            inserted += 1
            
            # Print batch updates every 5000 rows so it doesn't spam your terminal
            if inserted % 5000 == 0:
                logger.info(f" 🟩 Progress: {inserted}/{len(df)} rows safely migrated to MySQL.")
                
        except mysql.connector.Error as err:
            if err.errno == 1062:
                dupes += 1
            else:
                logger.error(f"Error on row {idx}: {err}")
                errors += 1
                
    conn.commit()
    cursor.close()
    conn.close()
    
    return inserted, dupes, errors

if __name__ == "__main__":
    # Point directly to your file
    csv_path = Path(r"data/mumbai_raw_kaggle.csv")
    
    if not csv_path.exists():
        logger.error(f"❌ CSV file not found at {csv_path}.")
        exit(1)
        
    logger.info(f"Reading target file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    inserted, dupes, errors = insert_kaggle_listings(df)
    
    print("\n" + "="*50)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("="*50)
    print(f" 🚀 Rows successfully added to MySQL: {inserted}")
    print(f" 🔁 Duplicate records skipped:        {dupes}")
    print(f" ❌ Row execution errors:             {errors}")
    print("="*50 + "\n")