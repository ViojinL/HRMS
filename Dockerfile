FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN addgroup --system hrms && adduser --system --ingroup hrms hrms
RUN mkdir -p /srv/hrms/staticfiles /srv/hrms/media
RUN chown -R hrms:hrms /srv/hrms

USER hrms

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
