FROM python:3.9-slim
WORKDIR /app
EXPOSE 8000
RUN pip install --no-cache-dir wheel
RUN pip install --no-cache-dir FastAPI uvicorn asyncpg pydantic pandas numpy
COPY . /app
CMD ["python", "index.py"]
