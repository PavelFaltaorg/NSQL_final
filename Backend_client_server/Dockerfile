FROM python:3.11-bullseye
WORKDIR /code
COPY requirements.txt /code
RUN pip install -r requirements.txt --no-cache-dir
COPY ./code /code
CMD python backend_client_server.py
