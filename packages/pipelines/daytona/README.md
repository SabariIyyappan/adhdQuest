# daytona — Game runtime (Person B)

The isolated environment where LLM-generated Python game code is written, validated,
run, and hot-reloaded mid-session.

## Snapshot: `adhdquest-pygame-base`

Built once (`snapshot/Dockerfile`) and registered in the Daytona dashboard so
`daytona.create()` is warm (< 90ms) instead of installing packages per session.
Contains Python 3.12, pygame/turtle/pyglet, Flask (WebSocket game server), the
`templates/` library, and `reload_level.py`.

```
snapshot/
  Dockerfile        Base image the snapshot is built from.
  build.sh          Build + register the snapshot.
templates/          Level scaffolding shipped inside the snapshot.
  __init__.py         build_game(spec) factory.
  base_level.py       Level ABC: input, scoring, event emission.
  mechanics/          One renderer per mechanic (maze, matching, quest, ...).
  score_tracker.py    Per-level fail counter -> Butterbase session events.
  server.py           Flask + WebSocket server rendered to an HTML canvas.
reload_level.py     Hot-reload a single level without restarting the process.
```

The Flask + canvas approach (not a raw pygame window) is the iframe-embeddable path —
see plan §10 risk register.
