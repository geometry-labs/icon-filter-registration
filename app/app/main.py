from fastapi import FastAPI

from .routers import broadcaster, id, log_event, transaction

app = FastAPI()

app.include_router(log_event.router)
app.include_router(transaction.router)
app.include_router(broadcaster.router)
app.include_router(id.router)
