import os
import pandas as pd
import pytest
from database.multi_market_db_logger import MultiMarketBESSDB

@pytest.fixture
def temp_multimarket_db(tmp_path):
    db_path = tmp_path / "test_multi_market.db"
    return MultiMarketBESSDB(db_name=str(db_path))

def test_multimarket_database_logging(temp_multimarket_db):
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
    
    count = temp_multimarket_db.save_dispatch_results(df_mock)
    assert count == 2
    
    import sqlite3
    conn = sqlite3.connect(temp_multimarket_db.db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM multi_market_logs")
    total_rows = cursor.fetchone()[0]
    conn.close()
    
    assert total_rows == 2
