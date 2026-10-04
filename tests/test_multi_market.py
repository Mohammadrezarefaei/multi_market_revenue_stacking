import unittest
import pandas as pd
import sqlite3
import os
import sys

# Add project root to sys.path to allow absolute imports from database package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.multi_market_db_logger import MultiMarketBESSDB

class TestMultiMarketDB(unittest.TestCase):
    def test_multimarket_database_logging(self):
        db_path = "test_multi_market.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        db = MultiMarketBESSDB(db_name=db_path)
        df_mock = pd.DataFrame({
            'hour': [0, 1],
            'da_price_eur': [45.5, 42.0],
            'afrr_price_eur': [12.0, 14.5],
            'solar_mw': [0.0, 0.0],
            'charge_mw': [1.0, 0.0],
            'discharge_mw': [0.0, 1.5],
            'afrr_mw': [0.5, 0.5],
            'soc_mwh': [3.0, 2.0]
        })
        
        count = db.save_dispatch_results(df_mock)
        self.assertEqual(count, 2)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM multi_market_logs")
        total_rows = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(total_rows, 2)
        
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == '__main__':
    unittest.main()
