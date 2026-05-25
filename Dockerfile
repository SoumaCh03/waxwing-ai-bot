FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system waxwing && adduser --system --ingroup waxwing waxwing

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

USER waxwing

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "src.main:app"]

