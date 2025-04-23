import os

# 数据库配置
DATABASE_PATH = os.path.join(os.getcwd(), "data", "financial_data.db")

# 计算参数
DISCOUNT_RATE = 0.1  # 折现率
GROWTH_RATE = 0.03   # 永续增长率

# 数据目录配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Excel模板配置
TEMPLATE_COLUMNS = [
    '报告日期', '营业收入', '净利润', '经营活动现金流',
    '资本支出', '总资产', '总负债', '金融资产',
    '长期股权投资', '少数股东权益比例', '总股本'
]

# 简单地创建目录
os.makedirs(DATA_DIR, exist_ok=True)

# 添加行业参数配置
INDUSTRY_GROWTH_LIMITS = {
    'default': 0.03,
    'technology': 0.05,
    'consumer': 0.04,
    'finance': 0.03,
    'energy': 0.02
}

# 添加估值参数范围
VALUATION_PARAMS = {
    'discount_rate': {
        'min': 0.05,
        'max': 0.15,
        'default': 0.10
    },
    'growth_rate': {
        'min': 0.00,
        'max': 0.05,
        'default': 0.03
    }
}
