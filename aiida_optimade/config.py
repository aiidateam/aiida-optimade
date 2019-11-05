import json
from pathlib import Path

from optimade.server.config import Config


class ServerConfig(Config):
    """Load config file"""

    ftype = "json"

    FILENAME = "config"

    page_limit = 500
    db_page_limit = 1000
    provider = "_aiida_"
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
        self.provider = config.get("provider", self.provider)
        self.provider_fields = set(config.get("provider_fields", self.provider_fields))


CONFIG = ServerConfig()
