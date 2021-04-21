FROM python:3.8-slim-buster
WORKDIR /app

RUN apt-get update && apt-get install -y libicu-dev pkg-config build-essential

RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --system --deploy --ignore-pipfile
COPY . .
CMD [ "python", "run_worker.py" ]
