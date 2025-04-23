import os
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import time
from functools import lru_cache
from data_collector import DataCollector
from equity_calculator import EquityCalculator
from database import FinancialData
import akshare as ak
import json

def get_stock_list():
    """获取股票列表，支持离线数据"""
    try:
        # 直接从akshare获取A股列表
        stock_list = ak.stock_info_a_code_name()
        if not stock_list.empty:
            # 添加市场类型信息
            stock_list['market'] = stock_list['code'].apply(
                lambda x: '上证' if x.startswith('6') else '深证' if x.startswith('000') else '创业板' if x.startswith('300') else '其他'
            )
            return stock_list
    except Exception as e:
        print(f"获取股票列表失败: {str(e)}")
        return pd.DataFrame(columns=['code', 'name', 'market'])

def search_stock(keyword):
    """搜索股票"""
    try:
        stock_list = get_stock_list()
        if stock_list.empty:
            print("无法获取股票列表")
            return pd.DataFrame()
        
        # 统一列名
        if '代码' in stock_list.columns:
            stock_list = stock_list.rename(columns={'代码': 'code', '名称': 'name'})
        
        # 需要增加以下功能：
        # 1. 支持沪深股票代码格式（如SH600519）
        # 2. 支持同时搜索代码和名称
        if keyword.upper().startswith(('SH', 'SZ')):
            code = keyword[2:]
            market_type = keyword[:2].upper()
            matches = stock_list[
                (stock_list['code'].str.contains(code)) & 
                (stock_list['market'].str.contains('上证' if market_type == 'SH' else '深证'))
            ]
        else:
            matches = stock_list[
                (stock_list['code'].str.contains(keyword)) | 
                (stock_list['name'].str.contains(keyword))
            ]
        
        # 添加限制，最多显示10条结果
        return matches.head(10)
        
    except Exception as e:
        print(f"搜索股票失败: {str(e)}")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="股权分析系统")
    subparsers = parser.add_subparsers(dest="command")

    # 创建模板命令
    template_parser = subparsers.add_parser("template", help="创建Excel模板")
    template_parser.add_argument("--output", type=str, help="输出文件路径")

    # 导入数据命令
    import_parser = subparsers.add_parser("import", help="导入数据")
    import_parser.add_argument("--file", type=str, help="Excel文件路径")
    import_parser.add_argument("--stock", type=str, help="股票代码")

    # 分析股票命令
    analyze_parser = subparsers.add_parser("analyze", help="分析股票价值")
    analyze_parser.add_argument("--stock", type=str, help="股票代码")
    analyze_parser.add_argument("--name", type=str, help="公司名称")
    analyze_parser.add_argument("--plot", action="store_true", help="是否显示图表")
    analyze_parser.add_argument("--output", type=str, help="输出文件路径")
    analyze_parser.add_argument("--verbose", action="store_true", help="显示详细信息")

    # 添加搜索命令
    search_parser = subparsers.add_parser("search", help="搜索股票")
    search_parser.add_argument("keyword", type=str, help="股票代码或公司名称关键词")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # 首次运行时更新数据库结构
        db = FinancialData()
        db.recreate_table()
        
        collector = DataCollector()
        calculator = EquityCalculator()  # 移到这里，避免重复创建
        
        if args.command == "template":
            print("正在创建Excel模板...")
            if collector.create_template(args.output):
                print("模板创建成功！")
            
        elif args.command == "import":
            if not args.file or not os.path.exists(args.file):
                print("错误：请提供有效的Excel文件路径")
                return
            if not args.stock:
                print("错误：请提供股票代码")
                return
                
            print(f"正在导入股票 {args.stock} 的数据...")
            collector.import_from_excel(args.file, args.stock)
            print("数据导入成功！")
            
        elif args.command == "search":
            matches = search_stock(args.keyword)
            if len(matches) == 0:
                print(f"未找到包含 '{args.keyword}' 的股票")
            else:
                print(f"\n找到 {len(matches)} 个匹配的股票:")
                for _, row in matches.iterrows():
                    market = row.get('market', '未知')
                    print(f"股票代码: {row['code']}, 公司名称: {row['name']}, 市场: {market}")
                if len(matches) == 10:
                    print("\n(仅显示前10条结果)")
                    
        elif args.command == "analyze":
            if args.name or args.stock:
                keyword = args.name if args.name else args.stock
                matches = search_stock(keyword)
                
                if len(matches) == 0:
                    print(f"未找到股票: {keyword}")
                    return
                elif len(matches) > 1:
                    print("\n找到多个匹配的股票:")
                    for _, row in matches.iterrows():
                        print(f"股票代码: {row['code']}, 公司名称: {row['name']}")
                    return
                
                stock_code = matches.iloc[0]['code']
                company_name = matches.iloc[0]['name']
                print(f"找到股票: {company_name} ({stock_code})")
                
                # 自动获取数据
                print("正在获取最新财务数据...")
                collector.collect_from_akshare(stock_code, company_name)
                
                # 分析数据
                print("开始分析...")
                result = calculator.calculate_equity_value(stock_code, verbose=args.verbose)
                
                print("\n分析结果:")
                print(f"企业价值: {result['enterprise_value']:,.2f}")
                print(f"股权价值: {result['equity_value']:,.2f}")
                print(f"每股价值: {result['per_share_value']:,.2f}")
                
                if args.plot:
                    calculator.plot_fcf_trend(stock_code, result['fcf_list'])
                    plt.show()
                    
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(f"股票代码: {stock_code}\n")
                        f.write(f"企业价值: {result['enterprise_value']:,.2f}\n")
                        f.write(f"股权价值: {result['equity_value']:,.2f}\n")
                        f.write(f"每股价值: {result['per_share_value']:,.2f}\n")
                    print(f"\n分析报告已保存至: {args.output}")
            else:
                print("请提供股票代码或公司名称")
                
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()
