"""Optional FastAPI benchmark adapter, without runtime dependencies."""

from fastapi import APIRouter, FastAPI, Request, Response

from .workloads import response

router = APIRouter()


@router.api_route("/bench/plain", methods=["GET", "HEAD"])
@router.api_route("/bench/json", methods=["GET", "HEAD"])
@router.post("/bench/echo")
async def bench(request: Request):
    status, headers, content = response(request.url.path, request.method, await request.body())
    return Response(
        content=content,
        status_code=status,
        headers={name.decode("ascii"): value.decode("ascii") for name, value in headers},
    )


app = FastAPI()
app.include_router(router)
