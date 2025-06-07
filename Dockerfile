FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e . --no-cache-dir
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "ask_bot"]
