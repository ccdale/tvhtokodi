import importlib
import sys
import types


def _load_remotefiles(monkeypatch, cfg=None, expanded_path="/home/test/.ssh/id_ed25519"):
    """Import tvhtokodi.remotefiles with a stub tvhtokodi.config module."""
    if cfg is None:
        cfg = {"tvhhost": "mediahost", "tvhuser": "mediauser", "keyfn": "id_ed25519"}

    config_mod = types.ModuleType("tvhtokodi.config")
    config_mod.readConfig = lambda: cfg
    config_mod.writeConfig = lambda: None
    config_mod.expandPath = lambda _path: expanded_path

    monkeypatch.setitem(sys.modules, "tvhtokodi.config", config_mod)
    sys.modules.pop("tvhtokodi.remotefiles", None)
    return importlib.import_module("tvhtokodi.remotefiles")


def test_remoteCommand_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    class FakeConnection:
        def __init__(self, host, user, connect_kwargs):
            calls["host"] = host
            calls["user"] = user
            calls["connect_kwargs"] = connect_kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def run(self, cmd, hide=True):
            calls["cmd"] = cmd
            calls["hide"] = hide
            return types.SimpleNamespace(exited=0, stdout="  done  \n")

    monkeypatch.setattr(remotefiles, "Connection", FakeConnection)

    result = remotefiles.remoteCommand("ls -la")

    assert result == "done"
    assert calls["host"] == "mediahost"
    assert calls["user"] == "mediauser"
    assert calls["connect_kwargs"] == {"key_filename": "/home/test/.ssh/id_ed25519"}
    assert calls["cmd"] == "ls -la"
    assert calls["hide"] is True


def test_remoteCommand_failure_exit_code(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)

    class FakeConnection:
        def __init__(self, host, user, connect_kwargs):
            self.host = host
            self.user = user
            self.connect_kwargs = connect_kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def run(self, cmd, hide=True):
            return types.SimpleNamespace(exited=1, stdout="ignored")

    monkeypatch.setattr(remotefiles, "Connection", FakeConnection)

    result = remotefiles.remoteCommand("false")

    assert result == ""


def test_remoteCommand_banner(monkeypatch, capsys):
    remotefiles = _load_remotefiles(monkeypatch)

    class FakeConnection:
        def __init__(self, host, user, connect_kwargs):
            self.host = host
            self.user = user
            self.connect_kwargs = connect_kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def run(self, cmd, hide=True):
            return types.SimpleNamespace(exited=0, stdout="ok")

    monkeypatch.setattr(remotefiles, "Connection", FakeConnection)

    result = remotefiles.remoteCommand("uptime", banner=True)
    out, _err = capsys.readouterr()

    assert result == "ok"
    assert "Running remote command on mediahost: uptime" in out


def test_remoteCommand_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom():
        raise RuntimeError("broken config")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "readConfig", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)
    monkeypatch.setattr(remotefiles, "sys", sys, raising=False)

    result = remotefiles.remoteCommand("hostname")

    assert result == ""
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)
    assert calls["exc"] is not None