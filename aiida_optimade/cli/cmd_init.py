from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
from tqdm import tqdm

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.common.logger import LOGGER, disable_logging

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator
    from typing import IO

    from aiida.common.extendeddicts import AttributeDict


@cli.command()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Force re-calculation of all OPTIMADE fields from the AiiDA database.",
)
@click.option(
    "-q",
    "--silent",
    is_flag=True,
    default=False,
    show_default=True,
    help="Suppress informational output.",
)
@click.option(
    "-m",
    "--mongo",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Create a MongoDB collection for the OPTIMADE fields instead of storing as a "
        "Node extra."
    ),
)
@click.option(
    "--filename",
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    help="Filename to load as database (currently only usable for MongoDB).",
)
@click.pass_obj
def init(obj: AttributeDict, force: bool, silent: bool, mongo: bool, filename: str):
    """Initialize an AiiDA database to be served with AiiDA-OPTIMADE."""
    from aiida import load_profile
    from aiida.cmdline.utils import echo

    # The default aiida.cmdline loglevel inherit from aiida loglevel is REPORT
    # Here we use INFO loglevel for the operations
    echo.CMDLINE_LOGGER.setLevel("INFO")

    filename_path = Path(filename)

    if mongo and filename_path:
        profile: str | None = f"MongoDB JSON file {filename_path.name}"
    else:
        try:
            profile = obj.profile.name
        except AttributeError:
            profile = None
        profile = load_profile(profile).name

    try:
        with disable_logging():
            from aiida_optimade.routers.structures import STRUCTURES

            if mongo:
                from optimade.server.config import CONFIG, SupportedBackend

                from aiida_optimade.routers.structures import STRUCTURES_MONGO

        if force:
            # Remove all OPTIMADE-specific extras / dropping MongoDB collection
            if mongo:
                if not silent:
                    echo.echo_warning(
                        "Forcing re-calculation. About to drop structures collection "
                        f"{STRUCTURES_MONGO.collection.full_name!r} in MongoDB."
                    )
                STRUCTURES_MONGO.collection.drop()
                if not silent:
                    echo.echo_info(
                        f"Done dropping {STRUCTURES_MONGO.collection.full_name!r} "
                        "collection."
                    )
            else:
                extras_key = STRUCTURES.resource_mapper.PROJECT_PREFIX.split(".")[1]
                query_kwargs = {
                    "filters": {"extras": {"has_key": extras_key}},
                    "project": "*",
                }

                number_of_nodes = STRUCTURES.count(**query_kwargs)
                if not silent:
                    echo.echo_info(
                        "Forcing re-calculation. About to remove OPTIMADE-specific "
                        f"extras for {number_of_nodes} Nodes."
                    )
                    echo.echo_warning("This may take several seconds!")

                all_calculated_nodes: list | tqdm = STRUCTURES._find_all(**query_kwargs)

                if not silent:
                    all_calculated_nodes = tqdm(
                        all_calculated_nodes,
                        desc=f"Removing {extras_key!r} extras",
                        leave=False,
                    )

                for (node,) in all_calculated_nodes:
                    node.delete_extra(extras_key)
                    del node
                del all_calculated_nodes

                if not silent:
                    echo.echo_info(
                        f"Done removing extra {extras_key!r} in {number_of_nodes} "
                        "Nodes."
                    )

        if not silent:
            echo.echo_info(f"Initializing {profile}.")
            echo.echo_warning("This may take several minutes!")

        if filename_path:
            if not mongo:
                LOGGER.debug(
                    "Passed filename (%s) with AiiDA backend (mongo=%s)",
                    filename,
                    mongo,
                )
                raise NotImplementedError(
                    "Passing a filename currently only works for a MongoDB backend"
                )

            import bson.json_util

            updated_pks: range | list[int] = range(len(STRUCTURES_MONGO))
            chunk_size = 2**24  # 16 MB

            if updated_pks and not silent:
                echo.echo_warning(
                    "Detected existing structures in collection. This will make the "
                    "initialization slower! If you wish to avoid the slow down "
                    "consider using --force to first drop the collection, if possible."
                )

            with open(filename_path) as handle:
                if TYPE_CHECKING:  # pragma: no cover
                    all_chunks: Generator[str | bytes, None, None] | tqdm

                if silent:
                    all_chunks = read_chunks(handle, chunk_size=chunk_size)
                else:
                    all_chunks = tqdm(
                        read_chunks(handle, chunk_size=chunk_size),
                        total=(filename_path.stat().st_size // chunk_size)
                        + (1 if filename_path.stat().st_size % chunk_size else 0),
                        desc=f"Storing entries in {filename_path.name}",
                    )
                if updated_pks:
                    for data in get_documents(all_chunks):  # type: ignore[arg-type]
                        for doc in bson.json_util.loads(data):
                            STRUCTURES_MONGO.collection.replace_one(
                                {"id": doc["id"]}, doc, upsert=True
                            )
                else:
                    for data in get_documents(all_chunks):  # type: ignore[arg-type]
                        STRUCTURES_MONGO.collection.insert_many(
                            bson.json_util.loads(data)
                        )
            updated_pks = range(len(STRUCTURES_MONGO) - len(updated_pks))
        else:
            entries_list: list[list[int]] = []
            if mongo:
                CONFIG.database_backend = SupportedBackend.MONGODB
                entries_set = {_[0] for _ in STRUCTURES._find_all(project="id")}
                entries_set -= {
                    int(_["id"])
                    for _ in STRUCTURES_MONGO.collection.find(
                        filter={}, projection=["id"]
                    )
                }
                entries_list = [[_] for _ in entries_set]

            STRUCTURES._extras_fields = {
                STRUCTURES.resource_mapper.get_backend_field(_)[
                    len(STRUCTURES.resource_mapper.PROJECT_PREFIX) :
                ]
                for _ in STRUCTURES.resource_mapper.ALL_ATTRIBUTES
                if STRUCTURES.resource_mapper.get_backend_field(_).startswith(
                    STRUCTURES.resource_mapper.PROJECT_PREFIX
                )
            }
            updated_pks = STRUCTURES._check_and_calculate_entities(
                cli=not silent,
                entries=entries_list if mongo else None,
            )
    except Exception as exc:  # noqa: BLE001
        import traceback

        exception = traceback.format_exc()

        LOGGER.error("Full exception from 'aiida-optimade init' CLI:\n%s", exception)
        echo.echo_critical(
            f"An exception happened while trying to initialize {profile} (see log "
            f"for more details):\n{exc!r}"
        )

    if not silent:
        if updated_pks:
            echo.echo_success(
                f"{profile} has been initialized for use with AiiDA-OPTIMADE. "
                f"{len(updated_pks)} StructureData and CifData Nodes or MongoDB "
                "documents have been initialized."
            )
        else:
            echo.echo_info(
                "No new StructureData and CifData Nodes or MongoDB documents found to "
                f"initialize for {profile}."
            )


def read_chunks(
    file_object: IO, chunk_size: int | None = None
) -> Generator[str | bytes, None, None]:
    """Generator to read a file piece by piece

    Parameters:
        file_object: The opened file or file-like object.
        chunk_size: Size of bytes/characters to read and yield (default size: 16 MB).

    Yields:
        Content from `file_object` of size `chunk_size` or less if it's the final
        content.

    """
    chunk_size = chunk_size if chunk_size and isinstance(chunk_size, int) else 2**24
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def get_documents(
    chunk_iterator: Generator[str | bytes, None, None],
) -> Generator[str, None, None]:
    """Generator to return MongoDB documents from file"""
    rest_chunk = ""

    for raw_chunk in chunk_iterator:
        full_raw_chunk: str = rest_chunk + (
            raw_chunk.decode("utf-8") if isinstance(raw_chunk, bytes) else raw_chunk
        )
        rest_chunk = ""

        curly_start_count = full_raw_chunk.count("{")
        curly_end_count = full_raw_chunk.count("}")

        if curly_start_count == 0 or curly_end_count == 0:
            rest_chunk = full_raw_chunk
            continue

        chunk = full_raw_chunk
        while curly_end_count - curly_start_count != 0:
            split_chunk = chunk.split("{")
            rest_chunk = "{" + f"{split_chunk[-1]}{rest_chunk}"
            chunk = "{".join(split_chunk[:-1])

            curly_start_count = chunk.count("{")
            curly_end_count = chunk.count("}")

            if curly_start_count == 0 or curly_end_count == 0:
                rest_chunk = chunk + rest_chunk
                chunk = ""
                break

        chunk = (
            chunk.strip()
            .lstrip(",")
            .rstrip(",")
            .strip()
            .lstrip("[")
            .rstrip("]")
            .strip()
        )

        if chunk:
            if not chunk.startswith("{") or not chunk.endswith("}"):
                msg = f"Chunk found, but it is not self-consistent:\n{chunk}"
                LOGGER.error(msg)
                raise SyntaxError(msg)
            yield f"[{chunk}]"
