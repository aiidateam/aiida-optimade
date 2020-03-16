FROM python:3.7

ENV AIIDA_PATH /app

WORKDIR /app

# Install specific optimade version
ARG OPTIMADE_TOOLS_VERSION=0.7.0
RUN pip install optimade==${OPTIMADE_TOOLS_VERSION}

# Install specific aiida-core version
ARG AIIDA_VERSION=1.1.1
RUN pip install aiida-core==${AIIDA_VERSION}

# Copy repo contents
COPY setup.py setup.json README.md ./
COPY aiida_optimade ./aiida_optimade
RUN pip install -e .

# Copy AiiDA configuration
COPY .docker/server_template.cfg ./server.cfg
COPY .docker/run.sh ./

EXPOSE 80

CMD ["/app/run.sh"]
