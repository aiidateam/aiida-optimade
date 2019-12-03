import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aiida_optimade.main import profile
from aiida_optimade.common import AiidaError

if profile.database_backend == "django":
    from aiida.orm.implementation.django.querybuilder import (
        DjangoQueryBuilder as QueryBuilder,
    )
    from aiida.orm.implementation.django.backend import DjangoBackend as Backend
elif profile.database_backend == "sqlalchemy":
    from aiida.orm.implementation.sqlalchemy.querybuilder import (
        SqlaQueryBuilder as QueryBuilder,
    )
    from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend as Backend
else:
    raise AiidaError(
        f'Unknown AiiDA backend "{profile.database_backend}" for profile {profile}'
    )


separator = ":" if profile.database_port else ""
engine_url = "postgresql://{user}:{password}@{hostname}{separator}{port}/{name}".format(
    separator=separator,
    user=profile.database_username,
    password=profile.database_password,
    hostname=profile.database_hostname,
    port=profile.database_port,
    name=profile.database_name,
)

engine = create_engine(
    engine_url,
    json_serializer=json.dumps,
    json_deserializer=json.loads,
    encoding="utf-8",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
        self.__optimade_session = SessionLocal()

    def query(self):
        """Special OPTiMaDe query()"""
        return OptimadeDjangoQueryBuilder(self, self.__optimade_session)

    def close(self):
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
        self.__optimade_session = SessionLocal()

    def query(self):
        """Special OPTiMaDe query()"""
        return OptimadeSqlaQueryBuilder(self, self.__optimade_session)

    def close(self):
        self.__optimade_session.close()
