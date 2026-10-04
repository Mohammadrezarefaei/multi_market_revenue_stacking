import sqlite3
import pandas as pd

class MultiMarketBESSDB:
    def __init__(self, db_name="multi_market_bess.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize database schema for multi-market dispatch and aFRR reserves."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS multi_market_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour INTEGER,
                da_price_eur REAL,
                afrr_price_eur REAL,
                solar_mw REAL,
                charge_mw REAL,
                discharge_mw REAL,
                afrr_mw REAL,
                soc_mwh REAL
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_dispatch_results(self, df_results):
        """Save optimized hourly dispatch and revenue stacking results to the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        for _, row in df_results.iterrows():
            cursor.execute('''
                INSERT INTO multi_market_logs (hour, da_price_eur, afrr_price_eur, solar_mw, charge_mw, discharge_mw, afrr_mw, soc_mwh)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(row['hour']),
                float(row['da_price_eur']),
                float(row['afrr_price_eur']),
                float(row['solar_mw']),
                float(row['charge_mw']),
                float(row['discharge_mw']),
                float(row['afrr_mw']),
                float(row['soc_mwh'])
            ))
            
        conn.commit()
        conn.close()
        return len(df_results)
