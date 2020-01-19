FROM python:3.7

ENV AIIDA_PATH /app

WORKDIR /app

RUN git clone https://github.com/Materials-Consortia/optimade-python-tools
RUN pip install -e optimade-python-tools
RUN pip install uvicorn

# copy repo contents
COPY setup.py setup.json README.md ./
COPY .ci/server_template.cfg ./server.cfg
COPY aiida_optimade ./aiida_optimade
RUN pip install -e .

# copy AiiDA configuration
COPY .docker/run.sh ./

EXPOSE 80

CMD ["/app/run.sh"]
