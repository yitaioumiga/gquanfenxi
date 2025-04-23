import pandas as pd
import os
import akshare as ak
from database import FinancialData
import time
import requests.exceptions
import json

class DataCollector:
    def __init__(self):
        self.db = FinancialData()
        self.example_data_path = os.path.join(os.path.dirname(__file__), 'data', 'example_data.json')

    def load_example_data(self, stock_code):
        """加载示例数据"""
        try:
            if os.path.exists(self.example_data_path):
                with open(self.example_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if stock_code in data:
                        return data[stock_code]
        except Exception as e:
            print(f"加载示例数据失败: {e}")
        return None

    def create_template(self, output_path=None):
        # 1. 准备路径
        try:
            if (output_path is None):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(current_dir, 'data')
                os.makedirs(data_dir, exist_ok=True)
                output_path = os.path.join(data_dir, 'template.xlsx')
            
            print(f"1. 输出路径: {output_path}")
            
            # 2. 创建数据
            data = {
                '报告日期': ['2023-12-31'],
                '营业收入': [100000000],
                '净利润': [10000000],
                '经营活动现金流': [15000000],
                '资本支出': [5000000],
                '总资产': [200000000],
                '总负债': [100000000],
                '金融资产': [20000000],
                '长期股权投资': [10000000],
                '少数股东权益比例': [0.1],
                '总股本': [100000000]
            }
            
            print("2. 创建示例数据")
            
            # 3. 创建DataFrame
            df = pd.DataFrame(data)
            print("3. DataFrame创建成功")
            
            # 4. 保存文件
            df.to_excel(output_path, index=False)
            print(f"4. 文件已保存: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"错误发生在create_template: {str(e)}")
            return False

    def import_from_excel(self, file_path, stock_code, company_name=None):
        try:
            print(f"1. 正在读取文件: {file_path}")
            df = pd.read_excel(file_path)
            
            # 验证必要列是否存在
            required_columns = [
                "报告日期", "营业收入", "净利润", "经营活动现金流",
                "资本支出", "总资产", "总负债", "金融资产",
                "长期股权投资", "少数股东权益比例", "总股本"
            ]
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Excel文件缺少必要列: {', '.join(missing_cols)}")
            
            print("2. 数据格式验证通过")
            
            # 检查是否有重复数据
            existing_data = self.db.get_stock_data(stock_code)
            existing_dates = [d['report_date'] for d in existing_data]
            
            # 如果没有提供公司名称，尝试从文件名获取
            if not company_name and '_' in os.path.basename(file_path):
                company_name = os.path.basename(file_path).split('_')[1].split('.')[0]

            # 导入数据
            imported_count = 0
            skipped_count = 0
            
            print("3. 开始导入数据...")
            for _, row in df.iterrows():
                if row["报告日期"] in existing_dates:
                    skipped_count += 1
                    continue
                    
                data = (
                    stock_code,
                    company_name,
                    str(row["报告日期"]),
                    float(row["营业收入"]),
                    float(row["净利润"]),
                    float(row["经营活动现金流"]),
                    float(row["资本支出"]),
                    float(row["总资产"]),
                    float(row["总负债"]),
                    float(row["金融资产"]),
                    float(row["长期股权投资"]),
                    float(row["少数股东权益比例"]),
                    float(row["总股本"]),
                )
                self.db.insert_data(data)
                imported_count += 1
            
            print(f"4. 导入完成")
            print(f"   - 新增数据: {imported_count} 条")
            print(f"   - 跳过重复: {skipped_count} 条")
            
            return True
            
        except Exception as e:
            print(f"导入失败: {str(e)}")
            return False

    def collect_from_akshare(self, stock_code, company_name=None):
        """从 akshare 自动获取数据"""
        print(f"正在获取 {stock_code} 的财务数据...")
        
        retries = 3
        for attempt in range(retries):
            try:
                # 先尝试从本地示例数据获取
                example_data = self.load_example_data(stock_code)
                if example_data:
                    print("使用示例数据...")
                    try:
                        self.db.delete_stock_data(stock_code)
                        for item in example_data['financial_data']:
                            data = (
                                stock_code,
                                company_name or example_data['company_name'],
                                item['report_date'],
                                item['revenue'],
                                item['net_profit'],
                                item['operating_cash_flow'],
                                item['capital_expenditure'],
                                item['total_assets'],
                                item['total_liabilities'],
                                item['financial_assets'],
                                item['long_term_investments'],
                                item['minority_interest_ratio'],
                                item['total_shares']
                            )
                            self.db.insert_data(data)
                        print("使用示例数据成功！")
                        return True
                    except Exception as e:
                        print(f"使用示例数据失败: {e}")

                # 如果示例数据不可用，尝试在线获取
                try:
                    print(f"尝试在线获取数据...")
                    print(f"正在获取 {stock_code} 的财务数据...")

                    # 尝试直接获取主要财务指标
                    try:
                        print("获取主要财务指标...")
                        df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")
                        df_income = ak.stock_financial_report_sina(stock=stock_code, symbol="利润表")
                        df_cash = ak.stock_financial_report_sina(stock=stock_code, symbol="现金流量表")

                        if all(not df.empty for df in [df, df_income, df_cash]):
                            print("成功获取财务报表数据")
                            
                            # 清理已有数据
                            self.db.delete_stock_data(stock_code)
                            
                            # 统一日期格式 - 使用'报告日'列
                            df['报告日'] = pd.to_datetime(df['报告日']).dt.strftime('%Y-%m-%d')
                            df_income['报告日'] = pd.to_datetime(df_income['报告日']).dt.strftime('%Y-%m-%d')
                            df_cash['报告日'] = pd.to_datetime(df_cash['报告日']).dt.strftime('%Y-%m-%d')
                            
                            # 获取共同的报告期
                            common_dates = (set(df['报告日']) & 
                                          set(df_income['报告日']) & 
                                          set(df_cash['报告日']))
                            
                            if not common_dates:
                                raise ValueError("未找到匹配的报告期")
                            
                            print(f"找到 {len(common_dates)} 个报告期的数据")
                            
                            # 字段映射更新为实际的列名
                            field_maps = {
                                'balance': {
                                    'total_assets': ['资产总计'],
                                    'total_liab': ['负债合计'],
                                    'cash': ['货币资金'],
                                    'long_inv': ['长期股权投资'],
                                    'total_share': ['实收资本(或股本)']
                                },
                                'income': {
                                    'revenue': ['营业总收入', '营业收入'],
                                    'net_profit': ['净利润', '归属于母公司所有者的净利润']
                                },
                                'cash_flow': {
                                    'operate_cash': ['经营活动产生的现金流量净额'],
                                    'invest_cash': ['购建固定资产、无形资产和其他长期资产所支付的现金']
                                }
                            }
                            
                            def get_value(df_row, field_list):
                                for field in field_list:
                                    if field in df_row.index and pd.notna(df_row[field]):
                                        return df_row[field]
                                return 0
                            
                            for date in sorted(common_dates):
                                try:
                                    b_row = df[df['报告日'] == date].iloc[0]
                                    i_row = df_income[df_income['报告日'] == date].iloc[0]
                                    c_row = df_cash[df_cash['报告日'] == date].iloc[0]
                                    
                                    def safe_float(val):
                                        try:
                                            if isinstance(val, str):
                                                val = val.replace(',', '')
                                            return float(val)
                                        except:
                                            return 0.0
                                    
                                    data = (
                                        stock_code,
                                        company_name,
                                        date,
                                        safe_float(get_value(i_row, field_maps['income']['revenue'])),
                                        safe_float(get_value(i_row, field_maps['income']['net_profit'])),
                                        safe_float(get_value(c_row, field_maps['cash_flow']['operate_cash'])),
                                        safe_float(get_value(c_row, field_maps['cash_flow']['invest_cash'])),
                                        safe_float(get_value(b_row, field_maps['balance']['total_assets'])),
                                        safe_float(get_value(b_row, field_maps['balance']['total_liab'])),
                                        safe_float(get_value(b_row, field_maps['balance']['cash'])),
                                        safe_float(get_value(b_row, field_maps['balance']['long_inv'])),
                                        0.1,  # 默认少数股东权益比例
                                        safe_float(get_value(b_row, field_maps['balance']['total_share']))
                                    )
                                    
                                    self.db.insert_data(data)
                                    print(f"已处理 {date} 的数据")
                                    
                                except Exception as e:
                                    print(f"处理 {date} 数据时出错: {str(e)}")
                                    continue
                            
                            return True
                            
                    except Exception as e:
                        print(f"获取主要财务指标失败: {str(e)}")
                    
                    # 如果上述方法失败，使用示例数据
                    print("使用示例数据...")
                    example_data = self.load_example_data(stock_code)
                    if example_data:
                        self.db.delete_stock_data(stock_code)
                        for item in example_data['financial_data']:
                            data = (
                                stock_code,
                                company_name or example_data['company_name'],
                                item['report_date'],
                                item['revenue'],
                                item['net_profit'],
                                item['operating_cash_flow'],
                                item['capital_expenditure'],
                                item['total_assets'],
                                item['total_liabilities'],
                                item['financial_assets'],
                                item['long_term_investments'],
                                item['minority_interest_ratio'],
                                item['total_shares']
                            )
                            self.db.insert_data(data)
                        print("使用示例数据成功！")
                        return True
                        
                except Exception as e:
                    print(f"数据获取失败: {str(e)}")
                    return False
                
            except Exception as e:
                if attempt < retries - 1:
                    print(f"重试 ({attempt + 1}/{retries})...")
                    time.sleep(1)
                else:
                    print(f"获取数据失败: {e}")
                    # 尝试使用保底数据
                    return self._use_fallback_data(stock_code, company_name)
        
        return False

    def _check_recent_data(self, stock_code):
        """检查是否已有最新数据"""
        data = self.db.get_stock_data(stock_code)
        if not data:
            return False
        
        latest_date = max(d['report_date'] for d in data)
        current_quarter = pd.Timestamp.now().quarter
        current_year = pd.Timestamp.now().year
        latest = pd.Timestamp(latest_date)
        
        # 如果已有本季度数据，直接使用
        return latest.year == current_year and latest.quarter >= current_quarter - 1

    def _use_fallback_data(self, stock_code, company_name=None):
        """使用保底数据"""
        try:
            # 先尝试使用示例数据
            example_data = self.load_example_data(stock_code)
            if example_data:
                return self._use_example_data(stock_code, company_name)
                
            # 如果没有示例数据，使用最基础估值数据
            basic_data = {
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'revenue': 1000000000,  # 10亿营收
                'net_profit': 100000000,  # 1亿利润
                'total_assets': 2000000000,  # 20亿资产
                'total_liabilities': 1000000000,  # 10亿负债
                'total_shares': 100000000  # 1亿股本
            }
            
            self.db.insert_data((
                stock_code,
                company_name,
                basic_data['report_date'],
                basic_data['revenue'],
                basic_data['net_profit'],
                0, # operating_cash_flow
                0, # capital_expenditure
                basic_data['total_assets'],
                basic_data['total_liabilities'],
                0, # financial_assets
                0, # long_term_investments
                0.1, # minority_interest_ratio
                basic_data['total_shares']
            ))
            return True
            
        except Exception as e:
            print(f"使用保底数据失败: {e}")
            return False
