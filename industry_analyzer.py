import os
import json
import time

class IndustryAnalyzer:
    def __init__(self):
        self.industry_data_path = os.path.join(os.path.dirname(__file__), 'data', 'industry_metrics.json')
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.industry_data_path), exist_ok=True)

    def get_industry_metrics(self, industry_name):
        """获取行业参数"""
        try:
            with open(self.industry_data_path, 'r', encoding='utf-8') as f:
                industry_data = json.load(f)
                return industry_data.get(industry_name, {})
        except FileNotFoundError:
            print(f"警告: 未找到行业数据文件 {self.industry_data_path}")
            return {}
        except json.JSONDecodeError:
            print(f"警告: 行业数据文件格式错误")
            return {}

    def suggest_growth_rate(self, industry_name, historical_growth):
        """智能建议永续增长率"""
        industry_metrics = self.get_industry_metrics(industry_name)
        industry_growth = industry_metrics.get('avg_growth_rate', 0.03)
        
        # 结合历史增长和行业平均得出建议值
        suggested_rate = min(
            (historical_growth + industry_growth) / 2,
            0.05  # 上限5%
        )
        return suggested_rate
