# Use an official Python runtime as a parent image
FROM python:3.10-alpine

# Lightweight container
COPY ./requirements.txt /requirements.txt
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers
RUN pip install -r /requirements.txt
RUN apk del .tmp

RUN mkdir /app
COPY ./app /app
WORKDIR /app

# Run Server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
