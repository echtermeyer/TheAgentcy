FROM python:3.11-slim
COPY . /app
WORKDIR /app

# Install dependencies using Poetry
RUN poetry install --no-dev
CMD ["poetry", "shell"]