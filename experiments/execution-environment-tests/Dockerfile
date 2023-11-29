FROM python:3.9-slim
WORKDIR /app
RUN pip install fastapi uvicorn
EXPOSE 8000
COPY test.py /app
CMD ["python", "test.py"]
