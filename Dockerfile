# syntax=docker/dockerfile:1
FROM python:3.9-alpine
ADD . /code
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers zlib-dev jpeg-dev libffi-dev 
RUN pip install -U  cffi pip setuptools
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run"]
