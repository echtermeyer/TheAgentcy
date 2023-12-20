# Use the specified base image
FROM docker/dev-environments-default:stable-1

# Install software-properties-common, pip, and other dependencies
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3 python3-pip && \
    # Install Poetry
    pip3 install poetry && \
    # Configure Poetry: Do not create virtualenvs inside the project
    poetry config virtualenvs.create true

# Copy the project files into the container
COPY . /app
WORKDIR /app

# Install dependencies using Poetry
RUN poetry install --no-dev
CMD ["poetry", "shell"]