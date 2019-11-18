FROM python:3.7

ENV AIIDA_PATH /app

WORKDIR /app

RUN pip install fastapi uvicorn

# copy repo contents
COPY setup.py ./
COPY aiida_optimade ./aiida_optimade
RUN pip install -e .

RUN git clone https://github.com/Materials-Consortia/optimade-python-tools
RUN cd optimade-python-tools && pip install -e .

# copy AiiDA configuration
COPY .docker/config.json ${AIIDA_PATH}/.aiida/

EXPOSE 80

CMD ["uvicorn", "aiida_optimade.main:app", "--host", "0.0.0.0", "--port", "80"]
