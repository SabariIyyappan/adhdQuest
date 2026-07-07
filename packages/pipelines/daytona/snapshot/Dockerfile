# adhdquest-pygame-base — pre-built Daytona snapshot (plan §5 snapshot strategy).
# Baking these deps + the template library means daytona.create() is warm (<90ms)
# instead of installing packages per session.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libsdl2-2.0-0 libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        pygame \
        pyglet \
        flask \
        flask-sock \
        httpx

WORKDIR /game

# Ship the template library + hot-reload script into the snapshot.
COPY templates/ ./templates/
COPY reload_level.py ./reload_level.py

EXPOSE 5000
