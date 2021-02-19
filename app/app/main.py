#  Copyright 2021 Geometry Labs, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
