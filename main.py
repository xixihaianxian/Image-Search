from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import exceptions,status
from schema import response as rp
from fastapi.middleware.cors import CORSMiddleware
from routers import retrieve

app=FastAPI()

app.mount(
    path="/static",
    app=StaticFiles(directory="./static"),
    name="static"
)

app.mount(
    path="/upload",
    app=StaticFiles(directory="./upload"),
    name="upload",
)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检索
app.include_router(retrieve.router)

@app.get("/ImageSearch")
def image_search():
    response=rp.success_response(message="Welcome to Image Search")
    return response