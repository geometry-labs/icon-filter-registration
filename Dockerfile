FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7 as base
COPY ./app /app
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

FROM base as prod

FROM base as test
COPY ./requirements_dev.txt /requirements_dev.txt
COPY ./tests /tests
RUN pip install -r /requirements_dev.txt
RUN python -m pytest ../tests
