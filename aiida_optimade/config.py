from typing import Optional

from pydantic import Field

from optimade.server.config import ServerConfig


class CustomServerConfig(ServerConfig):

    query_group: Optional[str] = Field(
        None,
        description="The AiiDA Group containing the data that will be served, allowing one to serve a curated set of data from a given database.",
    )


CONFIG: ServerConfig = CustomServerConfig()
