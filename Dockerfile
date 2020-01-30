FROM python:3.7

ENV AIIDA_PATH /app

WORKDIR /app

# Install specific optimade version
ARG OPTIMADE_TOOLS_VERSION=0.3.2
RUN pip install optimade==${OPTIMADE_TOOLS_VERSION}

# Copy repo contents
COPY setup.py setup.json README.md ./
COPY aiida_optimade ./aiida_optimade
RUN pip install -e .

# Copy AiiDA configuration
COPY .docker/server_template.cfg ./server.cfg
COPY .docker/run.sh ./

EXPOSE 80

CMD ["/app/run.sh"]
