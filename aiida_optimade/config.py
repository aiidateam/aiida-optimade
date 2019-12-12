import json
from typing import Any
from pathlib import Path

from optimade.server.config import Config, NoFallback


class ServerConfig(Config):
    """Load config file"""

    @staticmethod
    def _DEFAULTS(field: str) -> Any:
        res = {
            "version": "v1.0.0",
            "page_limit": 100,
            "db_page_limit": 500,
            "provider": {
                "prefix": "_aiida_",
                "name": "AiiDA",
                "description": "AiiDA: Automated Interactive Infrastructure and Database for Computational Science (http://www.aiida.net)",
                "homepage": "http://www.aiida.net",
                "index_base_url": None,
            },
            "provider_fields": {},
        }
        if field not in res:
            raise NoFallback(f"No fallback value found for '{field}'")
        return res[field]

    def __init__(self, server_cfg: Path = None):
        server = (
            Path(__file__).resolve().parent.parent.joinpath("server.cfg")
            if server_cfg is None
            else server_cfg
        )
        super().__init__(server)

    def load_from_json(self):
        """Load parameters from FILENAME.json"""

        with open(self._path) as config_file:
            config = json.load(config_file)

        self.version = config.get("version", self._DEFAULTS("version"))
        self.page_limit = int(config.get("page_limit", self._DEFAULTS("page_limit")))
        self.db_page_limit = int(
            config.get("db_page_limit", self._DEFAULTS("db_page_limit"))
        )
        self.provider = config.get("provider", self._DEFAULTS("provider"))
        self.provider_fields = config.get(
            "provider_fields", self._DEFAULTS("provider_fields")
        )


CONFIG = ServerConfig()
