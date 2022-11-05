ARG VERSION="3.10-alpine3.16"

FROM python:$VERSION as builder

WORKDIR /app


RUN pip install pipenv==v2022.10.10  && \
    apk add gcc g++ python3-dev libffi-dev

ENV PIPENV_VENV_IN_PROJECT=1

ADD Pipfile* ./
RUN pipenv install --dev --skip-lock


FROM python:$VERSION as prod

WORKDIR /app


ENV PIPENV_VENV_IN_PROJECT=1
RUN pip install pipenv==v2022.10.10

COPY --from=builder /app/ /app/

ADD app.py /app/
ADD sql.py /app/

EXPOSE 8000
#CMD ls;ls .venv
CMD pipenv run uvicorn app:app --host 0.0.0.0
