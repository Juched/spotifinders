FROM python:3

ADD . /code
WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install -r requirements.txt 
CMD gunicorn --bind 0.0.0.0:$PORT --workers 6 --threads 100 app:app