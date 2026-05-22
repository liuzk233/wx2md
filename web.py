"""wx2md Web - FastAPI 浏览器界面"""

import asyncio
import json
from pathlib import Path

import anyio.to_thread
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from wx2md import convert

app = FastAPI(title="wx2md")

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
                lambda: convert(url, on_progress=on_progress),
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
