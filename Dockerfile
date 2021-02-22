FROM python:3.8

WORKDIR /app

# Install specific optimade and aiida-core versions
ARG OPTIMADE_TOOLS_VERSION=0.13.0
ARG AIIDA_VERSION=1.5.2

# Copy repo contents
COPY setup.py setup.json README.md requirements*.txt ./
COPY aiida_optimade ./aiida_optimade

RUN pip install -U pip setuptools wheel \
    && pip install optimade==${OPTIMADE_TOOLS_VERSION} \
    && pip install aiida-core==${AIIDA_VERSION} \
    && reentry scan \
    && pip install -e .

COPY .docker/run.sh ./

EXPOSE 80

ARG CONFIG_FILE=aiida_optimade/config.json
COPY ${CONFIG_FILE} ./config.json
ENV OPTIMADE_CONFIG_FILE /app/config.json

CMD ["/app/run.sh"]
