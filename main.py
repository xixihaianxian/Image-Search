from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import exceptions,status

app=FastAPI()

app.mount(
    path="./static",
    app=StaticFiles(directory="./static"),
    name="static"
)

@app.get("/ImageSearch")
def image_search():
    return "ok"