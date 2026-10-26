from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from data_agent.api.deps import get_query_service
from data_agent.models.schemas.query import QueryRequest
from data_agent.services.query_service import QueryService

query_router = APIRouter(prefix="/query")


@query_router.post("")
async def search(
    query_request: QueryRequest,
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> StreamingResponse:
    return StreamingResponse(
        query_service.search(query_request.query), media_type="text/event-stream"
    )
