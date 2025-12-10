# blog_system

简体中文说明

## 项目简介
blog_system 是一个简单的 Flask 博客示例/小型系统，包含基本的应用入口、模型定义、配置和静态/模板文件。它使用 SQLite（提供了 `blog.db`）做为演示数据库，并包含可以直接运行或调试的脚本。

## 目录结构（主要文件）
- app.py — 应用主逻辑（或工厂函数）
- run.py — 启动/运行脚本
- simple_app.py — 简化演示版的应用
- models.py — 数据模型（ORM / DB 操作）
- simple_models.py — 简化的模型示例
- config.py — 配置项与默认配置
- requirements.txt — 依赖列表
- blog.db — SQLite 数据库文件（示例/演示数据）
- instance/ — (可选) 用于存放本地覆盖配置
- templates/ — Jinja2 模板
- static/ — 静态资源（CSS/JS/图片）
- utils/ — 工具函数
- __pycache__/ — Python 缓存（无需加入版本控制）

> 注：实际项目中可能包含更多子文件，请以仓库中实际内容为准。

## 环境与依赖
建议使用虚拟环境来隔离依赖：

1. 创建并激活虚拟环境
   - Unix / macOS:
     - python3 -m venv venv
     - source venv/bin/activate
   - Windows (PowerShell):
     - python -m venv venv
     - .\venv\Scripts\Activate.ps1

2. 安装依赖
   - pip install -r requirements.txt

（若需要特定 Python 版本，请参考项目作者说明或 requirements 中的提示）

## 配置
- 主配置在 `config.py`。
- `instance/` 目录可用于存放本地覆盖的配置文件（例如 `instance/config.py`），以避免将敏感信息提交到仓库。
- 如果需要自定义数据库路径、密钥或其他配置，请优先在 `instance/` 中进行覆盖。

## 运行（开发模式）
两种常见方式：

1. 直接运行脚本（如果 `run.py` 包含 app.run()）
   - python run.py

2. 使用 Flask 命令（若项目兼容）
   - export FLASK_APP=run.py  # 或在 Windows 上使用 set
   - export FLASK_ENV=development  # 可选，开启调试模式
   - flask run --host=0.0.0.0 --port=5000

启动后访问 http://127.0.0.1:5000 查看页面。

## 数据库
- 项目包含 `blog.db`（SQLite）作为示例数据库。
- 如果你想重建数据库或迁移，建议在代码中添加迁移脚本（如 Flask-Migrate）或提供初始化脚本以创建表并导入示例数据。

## 开发提示
- 在开发时，请使用虚拟环境并将本地配置放在 `instance/`。
- 如需添加用户认证、富文本编辑或文件上传，请把相应依赖加入 `requirements.txt` 并在 README 中补充使用说明。
- 如果准备生产部署，请替换 SQLite 为更健壮的数据库（Postgres/MySQL），并使用 WSGI 服务器（Gunicorn / uWSGI）进行托管。

## 贡献
欢迎提交 Issue 或 PR：
- 报告 bug 时请附上复现步骤和环境信息
- 提交功能请求时请描述用例与期望行为

## 许可证
项目未在此说明许可证的话，请在根目录添加 LICENSE 文件并注明使用许可（例如 MIT、Apache-2.0 等）。
