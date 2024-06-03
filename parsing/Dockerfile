# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-slim as base

# Update pip
RUN python -m pip install --upgrade pip

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

# Copy files if present
COPY *.py *.txt /app/

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r /app/requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Declare environment variables that can be passed at build time.
ARG USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68"
ARG ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
ARG TAG_STRONG_GROUPS="ჯგუფები/Groups"
ARG TAG_STRONG_TEACHERS="პედაგოგები/Teachers"
ARG TAG_STRONG_INFORMATICS="ინფორმატიკისა და მართვის სისტემების ფაკულტეტი/Faculty of Informatics and Control Systems"
ARG URL_LEQTORI="https://leqtori.gtu.ge"
ARG URL_REST=""
ARG N_FIRST_TABLES_TO_COLLECT=-1
ARG MAX_CONNECTIONS=10
ARG LOG_LEVEL="DEBUG"
ARG FORCE_TO_COLLECT="true"

ENV USER_AGENT=${USER_AGENT} \
    ACCEPT=${ACCEPT} \
    TAG_STRONG_GROUPS=${TAG_STRONG_GROUPS} \
    TAG_STRONG_TEACHERS=${TAG_STRONG_TEACHERS} \
    TAG_STRONG_INFORMATICS=${TAG_STRONG_INFORMATICS} \
    URL_LEQTORI=${URL_LEQTORI} \
    N_FIRST_TABLES_TO_COLLECT=${N_FIRST_TABLES_TO_COLLECT} \
    URL_REST=${URL_REST} \
    MAX_CONNECTIONS=${MAX_CONNECTIONS} \
    LOG_LEVEL=${LOG_LEVEL} \
    FORCE_TO_COLLECT=${FORCE_TO_COLLECT}

# Run the application.
CMD python ./main.py