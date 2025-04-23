import json
import pandas as pd
from datetime import datetime

def format_number(number):
    """格式化数字显示"""
    if number >= 100000000:
        return f"{number/100000000:.2f}亿"
    elif number >= 10000:
        return f"{number/10000:.2f}万"
    return f"{number:.2f}"

def validate_params(params):
    """验证参数合理性"""
    errors = []
    if params.get('growth_rate', 0) > 0.05:
        errors.append("永续增长率不应超过5%")
    if params.get('discount_rate', 0) < 0.05:
        errors.append("折现率不应低于5%")
    return errors

def parse_date(date_str):
    """统一日期格式"""
    return pd.to_datetime(date_str).strftime('%Y-%m-%d')
