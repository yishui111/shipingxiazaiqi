# -*- coding: utf-8 -*-
"""打包入口（PyInstaller 用 main.py 而非 app/server.py，避免相对导入问题）。

普通运行请直接使用：python -m app.server
"""
from app.server import main

if __name__ == "__main__":
    main()
