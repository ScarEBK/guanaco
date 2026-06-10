FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8080

ENV GUANACO_CONFIG_DIR=/data

CMD ["python", "railway-start.py"]