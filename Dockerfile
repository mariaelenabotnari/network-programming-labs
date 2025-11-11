FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir quart hypercorn
EXPOSE 8080
CMD ["python","Lab3/Server.py","8080","Lab3/Board.txt"]
