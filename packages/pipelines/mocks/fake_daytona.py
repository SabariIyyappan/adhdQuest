"""In-memory stand-in for the Daytona SDK (Person B owns the real integration).

Implements the subset of the SDK that ``pipelines.nodes.daytona_node`` uses:
``create`` / ``get`` returning a sandbox with ``.id``, ``.fs.upload_file``,
``.process.code_run`` / ``.process.exec``, ``.get_preview_link``, ``.stop``.

To stress the build critic loop, :attr:`fail_validations` makes the first N
``code_run(... --validate)`` calls exit non-zero (as if the LLM-authored game had a
bug) before succeeding. Every filesystem write and command is captured for tests.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _RunResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class _FakeFs:
    def __init__(self, sandbox: "FakeSandbox") -> None:
        self._sandbox = sandbox

    def upload_file(self, content: bytes, path: str) -> None:
        self._sandbox.files[path] = content


class _FakeProcess:
    def __init__(self, sandbox: "FakeSandbox") -> None:
        self._sandbox = sandbox

    def code_run(self, command: str) -> _RunResult:
        self._sandbox.commands.append(command)
        if "--validate" in command:
            self._sandbox.validate_attempts += 1
            dy = self._sandbox.daytona
            if self._sandbox.validate_attempts <= dy.fail_validations:
                return _RunResult(exit_code=1, stderr="SyntaxError: invalid game level")
            return _RunResult(exit_code=0, stdout="validation ok")
        return _RunResult(exit_code=0)

    def exec(self, command: str) -> _RunResult:
        self._sandbox.commands.append(command)
        return _RunResult(exit_code=0)


@dataclass
class FakeSandbox:
    daytona: "FakeDaytona"
    id: str
    files: dict[str, bytes] = field(default_factory=dict)
    commands: list[str] = field(default_factory=list)
    validate_attempts: int = 0
    stopped: bool = False

    def __post_init__(self) -> None:
        self.fs = _FakeFs(self)
        self.process = _FakeProcess(self)

    def get_preview_link(self, port: int = 5000) -> str:
        return f"https://{self.id}-{port}.sandbox-preview.daytona.local/"

    def stop(self) -> None:
        self.stopped = True


class FakeDaytona:
    def __init__(self, fail_validations: int = 0) -> None:
        # How many initial --validate runs should fail before succeeding.
        self.fail_validations = fail_validations
        self.sandboxes: dict[str, FakeSandbox] = {}

    def create(self, **kwargs: Any) -> FakeSandbox:
        sid = f"sbx_{uuid.uuid4().hex[:12]}"
        sandbox = FakeSandbox(daytona=self, id=sid)
        self.sandboxes[sid] = sandbox
        return sandbox

    def get(self, sandbox_id: str) -> FakeSandbox:
        if sandbox_id not in self.sandboxes:
            # Reconnecting to a warm sandbox that this process didn't create
            # (e.g. Pipeline 2 after a fresh restart) — materialize a stub.
            self.sandboxes[sandbox_id] = FakeSandbox(daytona=self, id=sandbox_id)
        return self.sandboxes[sandbox_id]
