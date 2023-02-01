from typing import Optional

from optimade.server.config import ServerConfig
from pydantic import Field


class CustomServerConfig(ServerConfig):
    query_group: Optional[str] = Field(
        None,
        description="The AiiDA Group containing the data that will be served, allowing one to serve a curated set of data from a given database.",
    )


CONFIG: ServerConfig = CustomServerConfig()
