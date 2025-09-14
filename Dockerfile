FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    build-base \
    libffi-dev \
    openssl-dev

# Install Poetry directly
RUN pip install poetry

# Set working directory
WORKDIR /action

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true

# Copy action code
COPY . .

# Install dependencies and package
RUN poetry install --only main

# Set entrypoint
ENV PYTHONPATH=/action/src
# Copy and make entrypoint script executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
