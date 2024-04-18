FROM node:21-alpine AS frontend

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci --no-scripts

COPY .babelrc webpack-production.config.js ./
COPY src/ src/

RUN npm run build

FROM python:3.8-alpine3.19

WORKDIR /usr/src/app

RUN apk add --no-cache libmagic

RUN pip install --no-cache-dir pipenv

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install

COPY *.py ./

COPY --from=frontend /app/build ./build/

CMD ["pipenv", "run", "gunicorn", "yoggi:yoggi", "-b", "0.0.0.0:3000", "--log-file", "-"]
