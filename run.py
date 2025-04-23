import os
import sys
import webbrowser
from time import sleep

def main():
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    
    # 启动API服务器
    print("正在启动服务器...")
    os.system("start python api_server.py")
    
    # 等待服务器启动
    sleep(2)
    
    # 打开浏览器
    print("正在打开浏览器...")
    webbrowser.open('http://localhost:5000')
    
    print("\n估值分析工具已启动!")
    print("按Ctrl+C退出...")
    
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        os.system("taskkill /f /im python.exe")

if __name__ == "__main__":
    main()
