#!/usr/bin/env python3
import sys
from pathlib import Path

import bson.json_util
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
collection = client["aiida_optimade"]["structures"]

data = bson.json_util.loads(
    Path(__file__)
    .parent.joinpath("test_structures_mongo.json")
    .read_text(encoding="utf8")
)

try:
    print(f"Inserting {len(data)} structures into {collection.full_name}")
    collection.insert_many(data, ordered=False)
except Exception as exc:  # pylint: disable=broad-except
    print("An error occurred!")
    sys.exit(exc)
else:
    print("Done!")
