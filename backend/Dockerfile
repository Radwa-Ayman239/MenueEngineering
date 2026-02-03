FROM python:3

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements/ requirements/

RUN pip install --no-cache-dir \
    -r requirements/base.txt \
    -r requirements/dev.txt \
    -r requirements/celery.txt \
    -r requirements/prod.txt

COPY . .

EXPOSE 8000
