from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from router.api import reviews
from router.graph.graph import graph
from router.schemas.state import DisruptionEvent
from router.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = get_settings()
    yield


app = FastAPI(
    title="A7 Disruption Router",
    description="Grounded exception routing for logistics disruptions",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(reviews.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/route")
def route_event(event: DisruptionEvent) -> dict[str, Any]:
    """Run a disruption event through the router graph."""
    thread_id = event.shipment_id
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"event": event.model_dump(), "messages": []}, config)
    return {"thread_id": thread_id, "state": result}
