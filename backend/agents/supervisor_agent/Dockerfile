FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}