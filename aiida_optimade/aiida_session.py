import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aiida_optimade.main import PROFILE
from aiida_optimade.common import AiidaError

if PROFILE.database_backend == "django":
    from aiida.orm.implementation.django.querybuilder import (
        DjangoQueryBuilder as QueryBuilder,
    )
    from aiida.orm.implementation.django.backend import DjangoBackend as Backend
elif PROFILE.database_backend == "sqlalchemy":
    from aiida.orm.implementation.sqlalchemy.querybuilder import (
        SqlaQueryBuilder as QueryBuilder,
    )
    from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend as Backend
else:
    raise AiidaError(
        f'Unknown AiiDA backend "{PROFILE.database_backend}" for profile {PROFILE}'
    )


SEPARATOR = ":" if PROFILE.database_port else ""
ENGINE_URL = "postgresql://{user}:{password}@{hostname}{separator}{port}/{name}".format(
    separator=SEPARATOR,
    user=PROFILE.database_username,
    password=PROFILE.database_password,
    hostname=PROFILE.database_hostname,
    port=PROFILE.database_port,
    name=PROFILE.database_name,
)

ENGINE = create_engine(
    ENGINE_URL,
    json_serializer=json.dumps,
    json_deserializer=json.loads,
    encoding="utf-8",
)

SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


class OptimadeDjangoQueryBuilder(QueryBuilder):
    """New DjangoQueryBuilder"""

    def __init__(self, backend, session):
        QueryBuilder.__init__(self, backend)
        self.__optimade_session = session

    def get_session(self):
        return self.__optimade_session


class OptimadeDjangoBackend(Backend):
    """New DjangoBackend"""

    def __init__(self):
        super().__init__()
        self.__optimade_session = SESSION_LOCAL()

    def query(self):
        """Special OPTiMaDe query()"""
        return OptimadeDjangoQueryBuilder(self, self.__optimade_session)

    def close(self):
        """Close custom session"""
        self.__optimade_session.close()


class OptimadeSqlaQueryBuilder(QueryBuilder):
    """New SqlaQueryBuilder"""

    def __init__(self, backend, session):
        QueryBuilder.__init__(self, backend)
        self.__optimade_session = session

    def get_session(self):
        return self.__optimade_session


class OptimadeSqlaBackend(Backend):
    """New SqlaBackend"""

    def __init__(self):
        super().__init__()
        self.__optimade_session = SESSION_LOCAL()

    def query(self):
        """Special OPTiMaDe query()"""
        return OptimadeSqlaQueryBuilder(self, self.__optimade_session)

    def close(self):
        """Close custom session"""
        self.__optimade_session.close()
