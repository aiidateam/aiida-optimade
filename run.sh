#!/bin/bash
export AIIDA_PROFILE="optimade_cod"
uvicorn aiida_optimade.main:app --reload --port 5000
