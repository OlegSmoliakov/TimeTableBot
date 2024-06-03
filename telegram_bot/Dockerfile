# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-alpine as base

# Update pip
RUN python -m pip install --upgrade pip && \
    apk update && apk add --no-cache curl ca-certificates

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# pydevd warning: Computing repr of soup (BeautifulSoup) was slow (took 2.75s) 
# Customize report timeout by setting the `PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT` 
# environment variable to a higher timeout (default is: 0.5s)
ENV PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT=1 

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
RUN adduser \
    --disabled-password \
    --gecos "" \
    appuser && \
    chown -R appuser:appuser /app

# Declare the GITHUB_TOKEN build argument
ARG GITHUB_TOKEN

# Copy files if present
COPY . /app/

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r /app/requirements.txt

# Compile translations
RUN pybabel compile -d src/locale -D base

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Declare environment variables that can be passed at build time.
ARG URL_REST="http://TEST"
ARG MAX_CONNECTIONS=1
ARG LOG_LEVEL="INFO"
ARG BOT_TOKEN=""

ENV URL_REST=${URL_REST} \
    MAX_CONNECTIONS=${MAX_CONNECTIONS} \
    LOG_LEVEL=${LOG_LEVEL} \
    BOT_TOKEN=${BOT_TOKEN}

# Run the application.
CMD python ./main.py