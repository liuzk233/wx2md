"""wx2md Web - FastAPI 浏览器界面"""

import asyncio
import json
import sys
import webbrowser
from pathlib import Path

import anyio.to_thread
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from wx2md import convert

app = FastAPI(title="wx2md")

# PyInstaller frozen 模式检测
IS_FROZEN = getattr(sys, "frozen", False)
BASE_DIR = Path(sys._MEIPASS) if IS_FROZEN else Path(__file__).resolve().parent
DATA_ROOT = Path(sys.executable).resolve().parent if IS_FROZEN else BASE_DIR
BROWSE_ROOT = DATA_ROOT.resolve()


def _list_drives():
    """列出 Windows 可用盘符"""
    import string
    drives = []
    for letter in string.ascii_uppercase:
        if Path(f"{letter}:\\").exists():
            drives.append(f"{letter}:")
    return drives


def _is_within_directory(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_browse_target(path: str) -> Path:
    if not path:
        return BROWSE_ROOT

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = BROWSE_ROOT / candidate
    return candidate.resolve()


def _resolve_output_dir(path: str) -> str:
    candidate = Path(path or "output")
    if not candidate.is_absolute():
        candidate = DATA_ROOT / candidate
    return str(candidate.resolve())


@app.get("/api/browse")
async def api_browse(path: str = Query(default="")):
    target = _resolve_browse_target(path)
    if not IS_FROZEN and not _is_within_directory(target, BROWSE_ROOT):
        return JSONResponse({"error": "目录访问被拒绝"}, status_code=403)
    if not target.is_dir():
        return JSONResponse({"error": "目录不存在"}, status_code=400)
    # 在盘符根目录（如 D:\）时列出盘符供选择
    if IS_FROZEN and path and len(path) <= 2 and Path(target.anchor).resolve() == target:
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
    if not IS_FROZEN and target == BROWSE_ROOT:
        parent = None
    else:
        parent = target.parent
    if parent == target:
        parent = None
    return {
        "current": str(target).replace("\\", "/"),
        "parent": str(parent).replace("\\", "/") if parent else None,
        "dirs": dirs,
        "drives": _list_drives() if IS_FROZEN and parent is None else None,
    }

# 确保 output 目录存在
DEFAULT_OUTPUT_DIR = DATA_ROOT / "output"
DEFAULT_OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(DEFAULT_OUTPUT_DIR)), name="output")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/convert")
async def api_convert(request: Request):
    body = await request.json()
    url = body.get("url", "")
    output_dir = _resolve_output_dir(body.get("output_dir", "output"))

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
    import socket
    import uvicorn

    def _find_available_port(start=8000, end=8009):
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        return None

    port = _find_available_port()
    if port is None:
        print("错误: 无法找到可用端口 (8000-8009)，请关闭占用端口的程序后重试。")
        sys.exit(1)

    host = "127.0.0.1" if IS_FROZEN else "0.0.0.0"

    if IS_FROZEN:
        webbrowser.open(f"http://{host}:{port}")

    uvicorn.run(app, host=host, port=port)
