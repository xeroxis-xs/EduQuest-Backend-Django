# Use an official Python runtime as a parent image
FROM python:3.10-alpine

# ENV PATH="/scripts:${PATH}"

ENV SECRET_KEY=${SECRET_KEY}
ENV ALLOWED_HOSTS=${ALLOWED_HOSTS}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}

# Lightweight container
COPY ./requirements.txt /requirements.txt
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers
RUN pip install -r /requirements.txt
RUN apk del .tmp

RUN mkdir /app
COPY ./app /app
WORKDIR /app
# COPY ./scripts /scripts

# RUN chmod +x /scripts/*

# RUN mkdir -p /vol/web/media
# RUN mkdir -p /vol/web/static
# RUN adduser -D user
# RUN chown -R user:user /vol
# RUN chmod -R 755 /vol/web
# USER user

# CMD ["entrypoint.sh"]

# Collect static files
RUN python manage.py collectstatic --noinput

# Run Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

# # Use an official Python runtime as a parent image
# FROM python:3.10-alpine

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Set the working directory in the container
# WORKDIR /app

# # Copy the requirements file into the container at /app
# COPY requirements.txt /app/

# # Install any needed packages specified in requirements.txt
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# # Copy the current directory contents into the container at /app
# COPY ./app/ /app/

# # Collect static files
# RUN python manage.py collectstatic --noinput

# # Run Gunicorn
# CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

