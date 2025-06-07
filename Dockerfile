FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e . --no-cache-dir
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
# Add healthcheck for Fly.io (optional but recommended)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/ || exit 1

CMD ["python", "-m", "ask_bot"]
