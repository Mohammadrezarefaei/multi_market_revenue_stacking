import unittest
import pandas as pd
import sqlite3
import os
from database.multi_market_db_logger import MultiMarketBESSDB

class TestMultiMarketDB(unittest.TestCase):
    def test_logging(self):
        db_path = "test_mm.db"
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
        total = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(total, 2)
        
        if os.path.exists(db_path):
            os.remove(db_path)
        print("All multi-market database unit tests passed successfully!")

if __name__ == '__main__':
    unittest.main()
