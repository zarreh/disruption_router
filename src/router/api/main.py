from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

from router.api import reviews
from router.graph.graph import graph
from router.observability import configure_logging, get_logger
from router.schemas.state import DisruptionEvent
from router.settings import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = get_settings()
    configure_logging()
    logger.info("disruption_router_startup")
    yield
    logger.info("disruption_router_shutdown")


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
    recommendation = result.get("recommendation")
    action = getattr(recommendation, "action", None) if recommendation else None
    logger.info("route_completed", thread_id=thread_id, action=action)
    return {"thread_id": thread_id, "state": result}


@app.post("/route/stream")
def stream_route_event(event: DisruptionEvent) -> EventSourceResponse:
    """Stream graph events for a disruption event via Server-Sent Events."""
    thread_id = event.shipment_id
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"event": event.model_dump(), "messages": []}

    async def event_generator() -> Any:
        for chunk in graph.stream(input_state, config, stream_mode="updates"):
            for node, update in chunk.items():
                yield {
                    "event": "node_update",
                    "data": {"node": node, "update": update},
                }
        yield {"event": "done", "data": {"thread_id": thread_id}}

    return EventSourceResponse(event_generator())
