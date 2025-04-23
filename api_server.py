import os
import time
from flask import Flask, jsonify, request, send_from_directory
from equity_calculator import EquityCalculator
from industry_analyzer import IndustryAnalyzer
from progress_tracker import ProgressTracker
from data_collector import DataCollector  # 添加这行
import akshare as ak
import json
import pandas as pd
from functools import lru_cache

app = Flask(__name__, static_folder='web')

# 添加静态文件服务
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

calculator = EquityCalculator()
industry_analyzer = IndustryAnalyzer()

# 添加缓存装饰器
@lru_cache(maxsize=1)
def get_stock_list_cached():
    """获取股票列表（带缓存）"""
    try:
        # 尝试从本地缓存文件读取
        cache_file = os.path.join('data', 'stock_list_cache.csv')
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, dtype={'code': str})
            if not df.empty:
                return df
    except Exception as e:
        print(f"读取缓存失败: {e}")
    
    # 从 akshare 获取
    try:
        df = ak.stock_info_a_code_name()
        if not df.empty:
            # 保存到缓存
            df.to_csv(cache_file, index=False)
            return df
    except Exception as e:
        print(f"从 akshare 获取数据失败: {e}")
        
    return pd.DataFrame()

@app.route('/api/search')
def search_stock():
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    try:
        stock_list = get_stock_list_cached()
        
        if stock_list.empty:
            return jsonify({
                'success': False,
                'message': '无法获取股票列表',
                'data': []
            })
            
        # 添加市场类型
        if 'market' not in stock_list.columns:
            stock_list['market'] = stock_list['code'].apply(
                lambda x: '上证' if str(x).startswith('6') 
                else '深证' if str(x).startswith('000') 
                else '创业板' if str(x).startswith('300') 
                else '其他'
            )
        
        # 搜索匹配（忽略大小写）
        if keyword.isdigit():
            matches = stock_list[stock_list['code'].str.contains(keyword, na=False)]
        else:
            matches = stock_list[
                stock_list['name'].str.contains(keyword, case=False, na=False)
            ]
            
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
            
        # 分页返回结果
        result = matches.iloc[start:end].to_dict('records')
        
        return jsonify({
            'success': True,
            'data': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        })

# 创建一个每个请求结束后关闭数据库连接的函数
@app.teardown_appcontext
def close_db(error):
    if hasattr(calculator, 'db'):
        calculator.db.close()
    if hasattr(industry_analyzer, 'db'):
        industry_analyzer.db.close()

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.json
        stock_code = data['stockCode']
        params = {
            'discount_rate': data.get('discountRate', 0.1),
            'growth_rate': data.get('growthRate', 0.03),
            'forecast_years': data.get('forecastPeriod', 5)
        }
        
        # 创建进度跟踪器
        progress = ProgressTracker(total_steps=5)
        
        # 先获取股票数据
        print(f"正在获取 {stock_code} 的财务数据...")
        progress.update("获取财务数据...")
        collector = DataCollector()
        if not collector.collect_from_akshare(stock_code):
            return jsonify({
                'success': False,
                'message': '获取财务数据失败',
                'data': None
            }), 500
        
        # 计算估值
        progress.update("计算估值...")
        result = calculator.calculate_equity_value(stock_code, params=params)
        
        # 统一响应格式
        response_data = {
            'success': True,
            'data': {
                'enterprise_value': result['enterprise_value'],
                'equity_value': result['equity_value'],
                'per_share_value': result['per_share_value'],
                'validation': {
                    'peRatio': result['validation']['pe_ratio'],
                    'pbRatio': result['validation']['pb_ratio'],
                    'evFcfRatio': result['validation']['ev_fcf_ratio']
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"分析失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
