from logging import getLogger, basicConfig, INFO, StreamHandler

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse

from auth.views import router as auth_router
from api.views import router as api_router

logger = getLogger()

FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"

stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
basicConfig(level=INFO, format=FORMAT, handlers=[stream_handler])

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(auth_router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount('/static', StaticFiles(directory='./static'), name='static')


@app.get("/")
def home_page():
    return {"message": "Это стартовое сообщение надеюсь у меня всё получиться"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app", reload=True
    )