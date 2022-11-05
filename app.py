import os
import string

import asyncpg as asyncpg
from fastapi import Depends, FastAPI
from pydantic import BaseModel, conint

import sql

app = FastAPI()


class Message(BaseModel):
    message: str


class EncodeRequest(Message):
    rot: conint(ge=0, lt=26)


class Stats(BaseModel):
    rot: int
    usages: int = 0


class StorageProvider:
    pool: asyncpg.Pool
    conf = (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', None) or 'postgres'}:"
        f"{os.getenv('POSTGRES_PASSWORD', None) or 'password'}@"
        f"{os.getenv('POSTGRES_HOST', None) or 'localhost'}:"
        f"{os.getenv('POSTGRES_PORT', None) or 5432}/"
        f"{os.getenv('POSTGRES_DATABASE', None) or 'postgres'}"
    )

    async def startup(self):
        self.pool = await asyncpg.create_pool(self.conf)

    async def __call__(self) -> asyncpg.Connection:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection

            async with conn.transaction():
                yield conn


temporary_storage: list[Stats] = []


@app.post("/encode", response_model=Message)
async def encode(
    data: EncodeRequest, conn: asyncpg.Connection = Depends(StorageProvider)
):
    sm = next(filter(lambda x: x.rot == data.rot, temporary_storage), None)
    if sm is None:
        sm = Stats(rot=data.rot)
        temporary_storage.append(sm)
    sm.usages += 1

    await conn.execute(sql.ADD_ROT, data.rot)

    return Message(message=__caesar_cipher(data.message, data.rot))


def __caesar_cipher(text: str, rot: int):
    return "".join(
        string.ascii_lowercase[abs(string.ascii_lowercase.index(i) + rot) % 26]
        for i in text
    )


@app.get("/decode", response_model=Message)
async def decode(data: EncodeRequest = Depends()):
    return Message(message=__caesar_cipher(data.message, -data.rot))


@app.get("/stats", response_model=list[Stats])
async def stats(conn: asyncpg.Connection = Depends(StorageProvider)):
    return list(map(lambda x: Stats(**x), await conn.fetch(sql.GET_STATS)))


storage = StorageProvider()
app.dependency_overrides[StorageProvider] = storage


@app.on_event("startup")
async def create_schemas():
    await storage.startup()
    await storage.pool.execute(sql.CREATE_DATABASE)
