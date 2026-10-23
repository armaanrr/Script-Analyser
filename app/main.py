from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .db import init_db
from .routes import router
from .screen2.routes import router as screen2_router
from .screen3.routes import router as screen3_router
from .screen4.routes import router as screen4_router
from .screen5.routes import router as screen5_router  
from .screen6.routes import router as screen6_router
from .screen7.routes import router as screen7_router
from .screen8.routes import router as screen8_router
from .screen9.routes import router as screen9_router
from .screen10.routes import router as screen10_router

app = FastAPI(title="Rocket Reels Script Analyzer")
init_db()

app.include_router(router)
app.include_router(screen2_router)
app.include_router(screen3_router)
app.include_router(screen4_router)
app.include_router(screen5_router) 
app.include_router(screen6_router)
app.include_router(screen7_router)
app.include_router(screen8_router)
app.include_router(screen9_router)
app.include_router(screen10_router)

STATIC = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/screen2")
def screen2():
    return FileResponse(STATIC / "screen2.html")


@app.get("/screen/{n}")
def screen(n: int):
    if n == 1:
        return FileResponse(STATIC / "index.html")
    if n == 2:
        return FileResponse(STATIC / "screen2.html")
    if 3 <= n <= 10:
        built = STATIC / f"screen{n}.html"
        return FileResponse(built if built.exists() else STATIC / "coming.html")
    raise HTTPException(404, "No such screen.")