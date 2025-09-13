FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    build-base \
    libffi-dev \
    openssl-dev

# Set working directory
WORKDIR /action

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy action code
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Set entrypoint
ENTRYPOINT ["python", "-m", "check_pr_issue_action.main"]
