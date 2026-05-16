from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from app.config.tortoise import TORTOISE_ORM
from app.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    ):
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/", tags=["test"])
async def root():
    return {"message": "Hello World"}

app.include_router(router)
