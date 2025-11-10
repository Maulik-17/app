from fastapi import FastAPI
import threading
from build_volumes import build_volumes

app = FastAPI()

running = False

def background_worker():
    global running
    running = True
    build_volumes()
    running = False


@app.get("/start")
def start():
    global running
    if running:
        return {"status": "already running"}
    thread = threading.Thread(target=background_worker)
    thread.start()
    return {"status": "started"}


@app.get("/status")
def status():
    return {"running": running}


@app.get("/ping")
def ping():
    return {"ok": True}
