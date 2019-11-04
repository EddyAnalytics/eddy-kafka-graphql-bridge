FROM python:3.7-slim as requirements

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv \
    && pipenv check    \
    && pipenv lock -r > /requirements.txt


FROM python:3.7-slim

WORKDIR /usr/src/app

COPY --from=requirements /requirements.txt .

RUN apt-get update \
    && apt-get install -y build-essential cmake flex bison \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y --purge build-essential cmake flex bison \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["eddy-kafka-graphql-bridge"]
