"""wx2md Web - FastAPI 浏览器界面"""

import asyncio
import json
from pathlib import Path

import anyio.to_thread
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from wx2md import convert

app = FastAPI(title="wx2md")

BASE_DIR = Path(__file__).resolve().parent


def _list_drives():
    """列出 Windows 可用盘符"""
    import string
    drives = []
    for letter in string.ascii_uppercase:
        if Path(f"{letter}:\\").exists():
            drives.append(f"{letter}:")
    return drives


@app.get("/api/browse")
async def api_browse(path: str = Query(default="")):
    if not path:
        target = BASE_DIR
    else:
        target = Path(path).resolve()
    if not target.is_dir():
        return JSONResponse({"error": "目录不存在"}, status_code=400)
    # 在盘符根目录（如 D:\）时列出盘符供选择
    if path and len(path) <= 2 and Path(target.anchor).resolve() == target:
        return {
            "current": str(target).replace("\\", "/"),
            "parent": None,
            "dirs": [],
            "drives": _list_drives(),
        }
    dirs = []
    try:
        for item in sorted(target.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                dirs.append(item.name)
    except PermissionError:
        pass
    parent = target.parent
    if parent == target:
        parent = None
    return {
        "current": str(target).replace("\\", "/"),
        "parent": str(parent).replace("\\", "/") if parent else None,
        "dirs": dirs,
        "drives": _list_drives() if parent is None else None,
    }

# 确保 output 目录存在
Path("output").mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.post("/api/convert")
async def api_convert(request: Request):
    body = await request.json()
    url = body.get("url", "")
    output_dir = body.get("output_dir", "output")

    if "mp.weixin.qq.com" not in url:
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'msg': '不是有效的微信公众号文章链接'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    queue = asyncio.Queue()

    def on_progress(msg):
        queue.put_nowait(msg)

    async def event_stream():
        task = asyncio.create_task(
            anyio.to_thread.run_sync(
                lambda: convert(url, output_dir=output_dir, on_progress=on_progress),
                cancellable=True,
            )
        )

        while not task.done():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                yield f"event: progress\ndata: {json.dumps({'msg': msg}, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                continue

        # 排空队列中剩余的进度消息
        while not queue.empty():
            msg = queue.get_nowait()
            yield f"event: progress\ndata: {json.dumps({'msg': msg}, ensure_ascii=False)}\n\n"

        try:
            result = task.result()
            yield f"event: done\ndata: {json.dumps(result, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'msg': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
