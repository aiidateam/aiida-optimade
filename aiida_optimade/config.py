import json
from pathlib import Path

from optimade.server.config import Config


class ServerConfig(Config):
    """Load config file"""

    ftype = "json"

    FILENAME = "config"

    page_limit = 500
    db_page_limit = 1000
    index_base_url = None
    provider = "_aiida_"
    provider_name = "AiiDA"
    provider_description = "AiiDA: Automated Interactive Infrastructure and Database for Computational Science (http://www.aiida.net)"
    provider_homepage = "http://www.aiida.net"
    provider_fields = set()

    def __init__(self, ftype: str = None, filename: str = None):
        self.FILENAME = self.FILENAME if filename is None else filename
        super().__init__(ftype)

    def load_from_json(self):
        """Load parameters from FILENAME.json"""

        with open(
            Path(__file__).resolve().parent.joinpath(self.FILENAME + ".json")
        ) as config_file:
            config = json.load(config_file)

        self.page_limit = int(config.get("page_limit", self.page_limit))
        self.db_page_limit = int(config.get("db_page_limit", self.db_page_limit))
        self.index_base_url = config.get("index_base_url", self.index_base_url)
        self.provider = config.get("provider", self.provider)
        self.provider_name = config.get("provider_name", self.provider_name)
        self.provider_description = config.get(
            "provider_description", self.provider_description
        )
        self.provider_homepage = config.get("provider_homepage", self.provider_homepage)
        self.provider_fields = set(config.get("provider_fields", self.provider_fields))


CONFIG = ServerConfig()
