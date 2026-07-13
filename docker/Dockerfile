#  Etapa 1: BUILD
FROM python:3.11-alpine AS builder
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#   Etapa 2: PRODUCCION
FROM python:3.11-alpine AS produccion
WORKDIR /app

# Crear usuario sin privilegios
RUN addgroup -S banconova && adduser -S banconova -G banconova

# Copiar dependencias y codigo
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --chown=banconova:banconova app/ .

# Variables de entorno
ENV AMBIENTE=desarrollo
ENV VERSION=1.0.0
ENV PORT=5000
ENV FLASK_DEBUG=false

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:5000/health || exit 1

USER banconova

# Usar gunicorn en produccion para mayor rendimiento
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
