#!/usr/bin/env python3
import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    try:
        # 动态导入，避免循环导入问题
        from app import app, init_db, monitor
        
        print("正在初始化数据库...")
        with app.app_context():
            init_db()
        
        print("启动网络监控...")
        monitor.start_background_task()
        
        print("博客系统启动成功!")
        print("访问地址: http://localhost:5000")
        print("测试账号: admin / admin123")
        print("按 Ctrl+C 停止服务")
        
        # 启动应用
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请检查项目文件是否完整")
        print("需要的文件: app.py, config.py, models.py, utils/")
    except Exception as e:
        print(f"启动错误: {e}")

if __name__ == '__main__':
    main()