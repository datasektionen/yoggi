FROM docker.io/node:23-alpine3.20 AS frontend
WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY webpack-production.config.js .babelrc ./
COPY src src

RUN npm run build

FROM docker.io/python:3.13-alpine3.20
WORKDIR /app

RUN apk add --no-cache libmagic

RUN python -m pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --deploy

COPY --from=frontend /app/build /app/build

COPY yoggi.py s3.py ./

CMD ["pipenv", "run", "gunicorn", "yoggi:yoggi"]
