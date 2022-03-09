from typing import Optional

from pydantic import Field

from optimade.server.config import ServerConfig


class CustomServerConfig(ServerConfig):

    query_group: Optional[str] = Field(
        None, description="The aiida group where curate the data for query."
    )


CONFIG: ServerConfig = CustomServerConfig()
