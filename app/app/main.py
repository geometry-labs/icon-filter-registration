from fastapi import FastAPI

from .routers import broadcaster, id, log_event, transaction
from .settings import settings

tags_metadata = [
    {
        "name": "broadcaster",
        "description": "Get broadcaster data.",
    },
    {
        "name": "modify",
        "description": "Get modify data.",
    },
    {
        "name": "id",
        "description": "Get event log data.",
    },
    {"name": "log_event"},
]


app = FastAPI(
    title="ICON Blockchain Event Registration REST API",
    description="Register events of type block, trnsaction, and event log "
    "with a broadcaster ... .",  # TODO add docs
    version="v0.1.0",
    openapi_tags=tags_metadata,
    openapi_url=f"{settings.DOCS_ENDPOINT_PREFIX}/openapi.json",
    docs_url=f"{settings.DOCS_ENDPOINT_PREFIX}",
)

app.include_router(log_event.router, prefix=settings.API_ENDPOINT_PREFIX)
app.include_router(transaction.router, prefix=settings.API_ENDPOINT_PREFIX)
app.include_router(broadcaster.router, prefix=settings.API_ENDPOINT_PREFIX)
app.include_router(id.router, prefix=settings.API_ENDPOINT_PREFIX)
