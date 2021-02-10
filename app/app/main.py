import uvicorn
from fastapi import FastAPI

from .routers import modify, register, status, unregister

app = FastAPI()

app.include_router(register.router)
app.include_router(unregister.router)
app.include_router(modify.router)
app.include_router(status.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
