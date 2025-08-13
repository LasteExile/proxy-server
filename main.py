import logging
import asyncio
from typing import Literal, Dict, Any

import requests
from requests.exceptions import RequestException
from fastapi import FastAPI, WebSocket as ServerWebSocket
from fastapi import Query
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from websockets.asyncio.client import connect as ClientWebSocket


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


app = FastAPI()


class RequestSchema(BaseModel):
    url: str
    method: Literal["get", "post", "put", "patch"] = "get"
    body: str | None = None
    query_params: Dict[str, Any] = {}
    headers: Dict[str, Any] = {}


@app.get("/health")
def health() -> JSONResponse:
    return {"ok": True}


@app.post("/send")
def send(
    schema: RequestSchema,
) -> Response:
    logger.error(f"Request with body: {schema.dict()}")
    response = requests.request(
        method=schema.method,
        url=schema.url,
        params=schema.query_params,
        headers=schema.headers,
        json=schema.body,
    ) 

    try:
        response.raise_for_status()
    except RequestException as e:
        raise HTTPException(str(e), status_code=405)

    return Response(str(response.text))


async def websocket_client_to_server(
    *,
    server_websocket: ServerWebSocket,
    client_websocket: ClientWebSocket,
) -> None:
    try:
        while True:
            msg = await server_websocket.receive_text()           
            await client_websocket.send(msg)                        
    except Exception:
        pass


async def websocket_server_to_client(
    *,
    server_websocket: ServerWebSocket,
    client_websocket: ClientWebSocket,
) -> None:
    try:
        while True:
            msg = await client_websocket.recv()                     
            await server_websocket.send_text(msg)                  
    except Exception:
        pass


@app.websocket("/ws")
async def ws(
    server_websocket: ServerWebSocket,
    url: str = Query(required=True),
):
    await server_websocket.accept()

    async with ClientWebSocket(url) as client_websocket:
        task1 = asyncio.create_task(websocket_client_to_server(
            server_websocket=server_websocket,
            client_websocket=client_websocket,
        ))
        task2 = asyncio.create_task(websocket_server_to_client(
            server_websocket=server_websocket,
            client_websocket=client_websocket,
        ))
        done, pending = await asyncio.wait(
            {task1, task2},
            return_when=asyncio.FIRST_COMPLETED
        )

        for t in pending:
            t.cancel()

        await asyncio.gather(*pending, return_exceptions=True)
        try:
            await server_websocket.close()
        except Exception:
            pass

@app.websocket("/ws-echo")
async def ws_echo(
    websocket: ServerWebSocket,
):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)

