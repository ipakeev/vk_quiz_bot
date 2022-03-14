FROM python:3.9.10-alpine
RUN apk add --no-cache libpq-dev postgresql-libs gcc musl-dev postgresql-dev libffi-dev
WORKDIR /usr/src/app
COPY . .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
ENTRYPOINT python main.py