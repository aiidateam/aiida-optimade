#!/bin/bash
export AIIDA_PROFILE="sohier_import_sqla"
uvicorn aiida_optimade.main:app --reload --port 5000
