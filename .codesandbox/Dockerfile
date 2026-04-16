FROM python:3.10.12

RUN apt-get update && apt-get install -y fish && \
    pip install -U pip && \
    pip install uv && \
    chsh -s /usr/bin/fish