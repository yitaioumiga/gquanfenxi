import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import akshare as ak
from database import FinancialData
from config import DISCOUNT_RATE, GROWTH_RATE
from industry_analyzer import IndustryAnalyzer

class EquityCalculator:
    def __init__(self):
        self.db = FinancialData()
        self.industry_analyzer = IndustryAnalyzer()
        
    def search_stock(self, keyword):
        """搜索股票"""
        try:
            stock_list = ak.stock_info_a_code_name()
            if stock_list.empty:
                return []
                
            if keyword.isdigit():
                matches = stock_list[stock_list['code'].str.contains(keyword)]
            else:
                matches = stock_list[stock_list['name'].str.contains(keyword)]
                
            return matches.to_dict('records')
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

    def calculate_free_cash_flow(self, data):
        return data.operating_cash_flow - data.capital_expenditure

    def calculate_enterprise_value(self, fcf_avg):
        return fcf_avg / (DISCOUNT_RATE - GROWTH_RATE)

    def get_industry_type(self, stock_code):
        """判断股票所属行业"""
        industry_mapping = {
            '600519': '消费',  # 茅台
            '600309': '化工',  # 万华化学
            '002594': '汽车',  # 比亚迪
            '000100': '科技',  # TCL科技
            '000725': '科技',  # 京东方
            '000063': '科技'   # 中兴通讯
        }
        return industry_mapping.get(stock_code, '其他')

    def calculate_equity_value(self, stock_code, verbose=False, params=None):
        """添加参数配置支持"""
        if params is None:
            params = {}
        
        # 使用配置的参数或默认值
        discount_rate = params.get('discount_rate', DISCOUNT_RATE)
        growth_rate = params.get('growth_rate', GROWTH_RATE)
        forecast_years = params.get('forecast_years', 5)
        
        # 添加参数合理性验证
        if growth_rate > 0.05:  # 5%
            print("警告: 永续增长率超过5%可能不合理")
        if discount_rate < 0.05:  # 5%
            print("警告: 折现率过低可能高估企业价值")

        data = self.db.get_stock_data(stock_code)
        
        if not data:
            raise ValueError(f"未找到股票代码 {stock_code} 的数据")
        
        # 过滤掉未来的数据和按日期排序
        current_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        valid_data = [d for d in data if d['report_date'] <= current_date]
        recent_data = sorted(valid_data, key=lambda x: x['report_date'], reverse=True)
        
        if len(recent_data) < 4:
            raise ValueError("数据量不足，至少需要4个季度的数据")
            
        # 只使用最近5年数据进行分析
        recent_data = recent_data[:20]
        print(f"\n使用最近 {len(recent_data)} 个季度的数据进行分析")
        
        # 分季度计算自由现金流
        fcf_by_quarter = {}
        for d in recent_data:
            quarter = pd.Timestamp(d['report_date']).quarter
            year = pd.Timestamp(d['report_date']).year
            
            if (year, quarter) not in fcf_by_quarter:
                fcf = d['operating_cash_flow'] - abs(d['capital_expenditure'])
                fcf_by_quarter[(year, quarter)] = fcf
        
        # 计算年化自由现金流（使用最近四个季度的平均值）
        recent_fcf = list(fcf_by_quarter.values())[:4]
        annual_fcf = sum(recent_fcf)
        
        # 计算历史增长率
        if len(recent_fcf) >= 8:
            prev_year_fcf = sum(list(fcf_by_quarter.values())[4:8])
            if prev_year_fcf > 0 and annual_fcf > 0:
                growth_rate = min((annual_fcf / prev_year_fcf) ** 0.25 - 1, GROWTH_RATE)
            else:
                growth_rate = GROWTH_RATE
        else:
            growth_rate = GROWTH_RATE
        
        # 使用最新的资产负债表数据
        latest_data = recent_data[0]
        
        # 修改现金流计算逻辑
        def calculate_normalized_fcf(recent_fcf):
            """计算标准化自由现金流"""
            if len(recent_fcf) >= 4:
                # 如果最近一年现金流为负，使用近3年平均
                if sum(recent_fcf[:4]) < 0:
                    all_positive_fcf = [f for f in recent_fcf if f > 0]
                    if all_positive_fcf:
                        return sum(all_positive_fcf) / len(all_positive_fcf) * 4
                return sum(recent_fcf[:4])
            return 0

        # 获取行业信息和特征
        industry_name = self.get_industry_type(stock_code)
        industry_metrics = self.get_industry_metrics(industry_name)
        
        # 计算年化指标
        latest_annual_revenue = latest_data['revenue'] * 4
        latest_annual_profit = latest_data['net_profit'] * 4
        net_assets = latest_data['total_assets'] - latest_data['total_liabilities']
        
        # 科技股特殊处理
        if industry_name == '科技':
            # 使用收入估值和净利润估值的加权平均
            if latest_annual_revenue > 0:
                ps_ratio = industry_metrics.get('ps_ratio', 3.0)
                revenue_based_value = latest_annual_revenue * ps_ratio
            else:
                revenue_based_value = net_assets * 2
                
            if latest_annual_profit > 0:
                pe_ratio = industry_metrics.get('avg_pe', 25)
                profit_based_value = latest_annual_profit * pe_ratio
            else:
                profit_based_value = revenue_based_value
            
            # 加权平均
            enterprise_value = (revenue_based_value * 0.4 + profit_based_value * 0.6)
            
        # 非科技股处理
        else:
            if annual_fcf > 0:
                # 正常DCF估值
                enterprise_value = annual_fcf * (1 + growth_rate) / (discount_rate - growth_rate)
            else:
                # 使用综合估值方法
                if latest_annual_profit > 0:
                    pe_value = latest_annual_profit * industry_metrics.get('avg_pe', 15)
                else:
                    pe_value = 0
                    
                pb_value = net_assets * industry_metrics.get('avg_pb', 1.5)
                ps_value = latest_annual_revenue * industry_metrics.get('ps_ratio', 1.0)
                
                # 加权平均
                if latest_annual_profit > 0:
                    enterprise_value = (pe_value * 0.5 + pb_value * 0.3 + ps_value * 0.2)
                else:
                    enterprise_value = (pb_value * 0.6 + ps_value * 0.4)

        # 计算股权价值
        financial_assets = latest_data['financial_assets'] or 0
        long_term_investments = latest_data['long_term_investments'] or 0
        total_liabilities = latest_data['total_liabilities'] or 0
        
        equity_value = (
            enterprise_value +
            financial_assets +
            long_term_investments -
            total_liabilities
        )
        
        # 确保结果合理性
        if equity_value < net_assets:
            equity_value = net_assets * industry_metrics.get('avg_pb', 1.5)
        
        # 计算每股价值
        minority_interest_ratio = latest_data['minority_interest_ratio'] or 0.1
        total_shares = latest_data['total_shares']
        
        per_share_value = (
            equity_value *
            (1 - minority_interest_ratio) /
            total_shares
        )
        
        # 打印详细信息
        print("\n计算过程:")
        print(f"最近四个季度自由现金流: {recent_fcf}")
        print(f"年化自由现金流 (FCF): {annual_fcf:,.2f}")
        print(f"折现率: {DISCOUNT_RATE:.2%}")
        print(f"增长率: {growth_rate:.2%}")
        print(f"企业价值: {enterprise_value:,.2f}")
        print(f"金融资产: {financial_assets:,.2f}")
        print(f"长期投资: {long_term_investments:,.2f}")
        print(f"总负债: {total_liabilities:,.2f}")
        print(f"少数股东权益比例: {minority_interest_ratio:.2%}")
        print(f"总股本: {total_shares:,.2f}")
        
        # 添加估值验证信息
        latest_data = recent_data[0]
        
        # 1. 市净率(PB)验证
        book_value = latest_data['total_assets'] - latest_data['total_liabilities']
        pb_ratio = equity_value / book_value
        
        # 2. 市盈率(PE)验证
        latest_net_profit = latest_data['net_profit'] * 4  # 年化
        pe_ratio = equity_value / latest_net_profit if latest_net_profit > 0 else float('inf')
        
        # 3. 企业价值倍数(EV/EBITDA)
        annual_fcf = sum(recent_fcf[:4])
        ev_fcf_ratio = enterprise_value / annual_fcf if annual_fcf > 0 else float('inf')
        
        # 打印估值验证信息
        print("\n估值合理性验证:")
        print(f"账面净资产: {book_value:,.2f}")
        print(f"市净率(P/B): {pb_ratio:.2f}x")
        print(f"年化净利润: {latest_net_profit:,.2f}")
        print(f"市盈率(P/E): {pe_ratio:.2f}x")
        print(f"企业价值/FCF: {ev_fcf_ratio:.2f}x")
        
        # 获取行业平均数据（可以从配置文件读取）
        industry_avg = {
            'pb_ratio': 2.5,  # 化工行业平均市净率
            'pe_ratio': 15,   # 化工行业平均市盈率
            'ev_fcf_ratio': 12 # 化工行业平均EV/FCF
        }
        
        print("\n行业对比:")
        print(f"行业平均市净率: {industry_avg['pb_ratio']:.2f}x")
        print(f"行业平均市盈率: {industry_avg['pe_ratio']:.2f}x")
        print(f"行业平均EV/FCF: {industry_avg['ev_fcf_ratio']:.2f}x")
        
        # 添加估值合理性判断
        is_reasonable = (
            0.5 <= pb_ratio <= 5.0 and
            5 <= pe_ratio <= 30 and
            5 <= ev_fcf_ratio <= 20
        )
        
        print(f"\n估值合理性: {'合理' if is_reasonable else '需要进一步验证'}")
        
        if verbose:
            print("\n===== 详细财务数据 =====")
            print("最近5年主要财务指标:")
            for i, d in enumerate(recent_data[:min(20, len(recent_data))]):
                print(f"\n{d['report_date']}:")
                print(f"  营业收入: {d['revenue']:,.2f}")
                print(f"  净利润: {d['net_profit']:,.2f}")
                print(f"  经营现金流: {d['operating_cash_flow']:,.2f}")
                print(f"  资本支出: {d['capital_expenditure']:,.2f}")
            
            print("\n===== 估值指标分析 =====")
            # 计算各类估值指标
            latest_revenue = latest_data['revenue'] * 4  # 年化收入
            latest_net_profit = latest_data['net_profit'] * 4  # 年化净利润
            ev_to_revenue = enterprise_value / latest_revenue if latest_revenue > 0 else float('inf')
            pb_ratio = equity_value / book_value if book_value > 0 else float('inf')
            pe_ratio = equity_value / latest_net_profit if latest_net_profit > 0 else float('inf')
            
            print(f"市销率(P/S): {ev_to_revenue:.2f}x")
            print(f"市净率(P/B): {pb_ratio:.2f}x")
            print(f"市盈率(P/E): {pe_ratio:.2f}x")
            
            print("\n===== 增长分析 =====")
            if len(recent_data) >= 8:
                yoy_revenue_growth = (latest_data['revenue'] / recent_data[4]['revenue'] - 1) * 100
                yoy_profit_growth = (latest_data['net_profit'] / recent_data[4]['net_profit'] - 1) * 100
                print(f"营收同比增长: {yoy_revenue_growth:.2f}%")
                print(f"利润同比增长: {yoy_profit_growth:.2f}%")
            
            print("\n===== 现金流分析 =====")
            print(f"经营现金流/净利润: {(latest_data['operating_cash_flow'] / latest_data['net_profit']):.2f}x")
            
            print("\n===== 资产负债分析 =====")
            debt_ratio = latest_data['total_liabilities'] / latest_data['total_assets']
            print(f"资产负债率: {debt_ratio:.2%}")
        
        # 返回结果时包含验证信息
        return {
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'per_share_value': per_share_value,
            'fcf_list': recent_fcf,
            'validation': {
                'pb_ratio': pb_ratio,
                'pe_ratio': pe_ratio,
                'ev_fcf_ratio': ev_fcf_ratio,
                'is_reasonable': is_reasonable
            }
        }

    def get_industry_metrics(self, industry_name):
        return self.industry_analyzer.get_industry_metrics(industry_name)

    def plot_fcf_trend(self, stock_code, fcf_list):
        if not fcf_list:
            raise ValueError("没有可用的自由现金流数据")
            
        plt.figure(figsize=(10, 6))
        plt.plot(fcf_list, marker='o')
        plt.title(f'自由现金流趋势图 - {stock_code}')
        plt.xlabel('季度')
        plt.ylabel('自由现金流（元）')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

    def analyze_stock(self, stock_code, plot=False, output=None):
        # 实现单只股票分析
        pass
        
    def compare_stocks(self, stock_codes, plot=False, output=None):
        # 实现多只股票对比
        pass
