import logging
from typing import Literal, Dict, Any

import requests
from requests.exceptions import RequestException
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import HTTPException
from pydantic import BaseModel


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

