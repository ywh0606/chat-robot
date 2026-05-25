import uvicorn
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("启动新服务在端口 8001...")
print("访问地址: http://localhost:8001")
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
