FROM python:alpine3.16
WORKDIR /app

RUN apk add --update --no-cache libffi libffi-dev icu icu-dev icu-data-full curl g++ make

ENV POETRY_VERSION=1.1.13

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

#RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
#RUN source $HOME/.poetry/env

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev
COPY . .
CMD [ "python", "run_worker.py" ]
