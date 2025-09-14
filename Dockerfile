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

# Install dependencies only (no root package)
RUN poetry install --only main --no-root

# Copy action code
COPY . .

# Install the current project
RUN poetry install --only main

# Set entrypoint
CMD ["poetry", "run", "python", "-m", "check_pr_issue_action.main"]
