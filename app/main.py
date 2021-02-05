from fastapi import FastAPI

from app.routers import modify, register, status, unregister

app = FastAPI()

app.include_router(register.router)
app.include_router(unregister.router)
app.include_router(modify.router)
app.include_router(status.router)
