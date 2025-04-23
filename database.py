import sqlite3
from config import DATABASE_PATH
import threading

class FinancialData:
    def __init__(self):
        self._connection = None
        self._local = threading.local()
        self.create_table()

    @property
    def conn(self):
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(DATABASE_PATH)
        return self._local.connection

    def close(self):
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            company_name TEXT,
            report_date TEXT NOT NULL,
            revenue REAL,
            net_profit REAL,
            operating_cash_flow REAL,
            capital_expenditure REAL,
            total_assets REAL,
            total_liabilities REAL,
            financial_assets REAL,
            long_term_investments REAL,
            minority_interest_ratio REAL,
            total_shares REAL
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def insert_data(self, data):
        query = """
        INSERT INTO financial_data (
            stock_code, company_name, report_date, revenue, net_profit, operating_cash_flow,
            capital_expenditure, total_assets, total_liabilities, financial_assets,
            long_term_investments, minority_interest_ratio, total_shares
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, data)
        self.conn.commit()

    def recreate_table(self):
        """重新创建表以添加新列"""
        self.conn.execute("DROP TABLE IF EXISTS financial_data")
        self.create_table()
        print("数据库表结构已更新")

    def get_stock_data(self, stock_code):
        try:
            query = "SELECT * FROM financial_data WHERE stock_code = ? ORDER BY report_date"
            cursor = self.conn.execute(query, (stock_code,))
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return []

    def get_stock_by_name(self, company_name):
        query = """
        SELECT DISTINCT stock_code, company_name 
        FROM financial_data 
        WHERE company_name LIKE ?
        """
        cursor = self.conn.execute(query, (f"%{company_name}%",))
        return cursor.fetchall()

    def delete_stock_data(self, stock_code):
        """删除股票数据"""
        query = "DELETE FROM financial_data WHERE stock_code = ?"
        self.conn.execute(query, (stock_code,))
        self.conn.commit()

    def __del__(self):
        self.close()
