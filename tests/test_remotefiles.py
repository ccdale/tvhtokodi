import importlib
import sys
import types

import tvhtokodi


def _load_remotefiles(monkeypatch, cfg=None, expanded_path="/home/test/.ssh/id_ed25519"):
    """Import tvhtokodi.remotefiles with patched tvhtokodi config values."""
    if cfg is None:
        cfg = {"sshhost": "mediahost", "sshuser": "mediauser", "keyfn": "id_ed25519"}

    monkeypatch.setattr(tvhtokodi, "cfg", cfg, raising=False)
    monkeypatch.setattr(tvhtokodi, "expandPath", lambda _path: expanded_path, raising=False)
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

    class BoomConnection:
        def __init__(self, host, user, connect_kwargs):
            raise RuntimeError("broken ssh")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "Connection", BoomConnection)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.remoteCommand("hostname")

    assert result == ""
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)
    assert calls["exc"] is not None


def test_allShowFiles_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}
    show = {
        "title": "My Show",
        "filename": "/srv/media/Shows/My Show.ts",
    }

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        calls["banner"] = banner
        return "/srv/media/Shows/My Show.ts\n/srv/media/Shows/My Show.txt"

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.allShowFiles(show)

    assert result == [
        "/srv/media/Shows/My Show.ts",
        "/srv/media/Shows/My Show.txt",
    ]
    assert calls["cmd"] == 'ls -1 "/srv/media/Shows/My Show"* 2>/dev/null || true'
    assert calls["banner"] is False


def test_allShowFiles_failure_exit_code(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    show = {
        "title": "My Show",
        "filename": "/srv/media/Shows/My Show.ts",
    }

    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "")

    result = remotefiles.allShowFiles(show)

    assert result == []


def test_allShowFiles_banner(monkeypatch, capsys):
    remotefiles = _load_remotefiles(monkeypatch)
    show = {
        "title": "My Show",
        "filename": "/srv/media/Shows/My Show.ts",
    }

    def fake_remoteCommand(cmd, banner=False):
        print("remoteCommand called", flush=True)
        return "/srv/media/Shows/My Show.ts"

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.allShowFiles(show, banner=True)
    out, _err = capsys.readouterr()

    assert result == ["/srv/media/Shows/My Show.ts"]
    assert "remoteCommand called" in out


def test_allShowFiles_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    show = {
        "title": "My Show",
        "filename": "/srv/media/Shows/My Show.ts",
    }
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("broken command")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.allShowFiles(show)

    assert result == []
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)
    assert calls["exc"] is not None


def test_cpRemoteFile_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        calls["banner"] = banner
        return ""

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.cpRemoteFile("/tmp/src.ts", "/tmp/dest.ts", banner=True)

    assert result is True
    assert calls["cmd"] == 'cp "/tmp/src.ts" "/tmp/dest.ts"'
    assert calls["banner"] is True


def test_cpRemoteFile_failure(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "error")

    result = remotefiles.cpRemoteFile("/tmp/src.ts", "/tmp/dest.ts")

    assert result is False


def test_cpRemoteFile_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("copy failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.cpRemoteFile("/tmp/src.ts", "/tmp/dest.ts")

    assert result is False
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)


def test_remoteFileSize_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return "2048"

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteFileSize("/tmp/video.ts", human=False)

    assert result == 2048
    assert calls["cmd"] == 'stat -c%s "/tmp/video.ts"'


def test_remoteFileSize_human_true(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return "2048"

    def fake_humanSize(sizebytes):
        calls["sizebytes"] = sizebytes
        return "2.00 KB"

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)
    monkeypatch.setattr(remotefiles, "humanSize", fake_humanSize)

    result = remotefiles.remoteFileSize("/tmp/video.ts", human=True)

    assert result == "2.00 KB"
    assert calls["cmd"] == 'stat -c%s "/tmp/video.ts"'
    assert calls["sizebytes"] == 2048


def test_remoteFileSize_missing(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "")

    result = remotefiles.remoteFileSize("/tmp/video.ts")

    assert result == -1


def test_remoteFileSize_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("stat failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.remoteFileSize("/tmp/video.ts")

    assert result == -1
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)


def test_remoteExists_file(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return ""

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteExists("/tmp/video.ts")

    assert result is True
    assert calls["cmd"] == 'test -f "/tmp/video.ts"'


def test_remoteExists_dir(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return ""

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteExists("/tmp/videos", isdir=True)

    assert result is True
    assert calls["cmd"] == 'test -d "/tmp/videos"'


def test_remoteExists_false(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "not found")

    result = remotefiles.remoteExists("/tmp/video.ts")

    assert result is False


def test_remoteFinalFileName_first_available(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"cmds": []}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmds"].append(cmd)
        return ""

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteFinalFileName("/srv/media/My Show.ts")

    assert result == "/srv/media/My Show.ts"
    assert calls["cmds"] == ['test -f "/srv/media/My Show.ts"']


def test_remoteFinalFileName_with_suffix(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"cmds": []}
    responses = iter(["exists", "exists", ""])

    def fake_remoteCommand(cmd, banner=False):
        calls["cmds"].append(cmd)
        return next(responses)

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteFinalFileName("/srv/media/My Show.ts")

    assert result == "/srv/media/My Show-2.ts"
    assert calls["cmds"] == [
        'test -f "/srv/media/My Show.ts"',
        'test -f "/srv/media/My Show-1.ts"',
        'test -f "/srv/media/My Show-2.ts"',
    ]


def test_remoteFinalFileName_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("probe failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.remoteFinalFileName("/srv/media/My Show.ts")

    assert result == "/srv/media/My Show.ts"
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)


def test_remoteSHA256_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return "0123456789abcdef  /tmp/video.ts"

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteSHA256("/tmp/video.ts")

    assert result == "0123456789abcdef"
    assert calls["cmd"] == 'sha256sum "/tmp/video.ts"'


def test_remoteSHA256_empty(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "")

    result = remotefiles.remoteSHA256("/tmp/video.ts")

    assert result == ""


def test_remoteSHA256_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("hash failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.remoteSHA256("/tmp/video.ts")

    assert result == ""
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)


def test_remoteMkdir_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {}

    def fake_remoteCommand(cmd, banner=False):
        calls["cmd"] = cmd
        return ""

    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.remoteMkdir("/srv/newdir")

    assert result is True
    assert calls["cmd"] == 'mkdir -p "/srv/newdir"'


def test_remoteMkdir_failure(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "mkdir: error")

    result = remotefiles.remoteMkdir("/srv/newdir")

    assert result is False


def test_remoteMkdir_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(cmd, banner=False):
        raise RuntimeError("mkdir failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteCommand", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.remoteMkdir("/srv/newdir")

    assert result is False
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)


def test_moveTVFiles_dest_exists_returns_false(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"mkdir_called": 0}

    monkeypatch.setattr(remotefiles, "remoteExists", lambda destdir, isdir=False: True)

    def fake_mkdir(destdir):
        calls["mkdir_called"] += 1
        return True

    monkeypatch.setattr(remotefiles, "remoteMkdir", fake_mkdir)

    result = remotefiles.moveTVFiles(["/src/a.ts"], "/dest")

    assert result is False
    assert calls["mkdir_called"] == 0


def test_moveTVFiles_mkdir_fails_returns_false(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)

    monkeypatch.setattr(remotefiles, "remoteExists", lambda destdir, isdir=False: False)
    monkeypatch.setattr(remotefiles, "remoteMkdir", lambda destdir: False)

    result = remotefiles.moveTVFiles(["/src/a.ts"], "/dest")

    assert result is False


def test_moveTVFiles_move_command_failure(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)

    monkeypatch.setattr(remotefiles, "remoteExists", lambda destdir, isdir=False: False)
    monkeypatch.setattr(remotefiles, "remoteMkdir", lambda destdir: True)
    monkeypatch.setattr(remotefiles, "remoteFileSize", lambda fn: 100)
    monkeypatch.setattr(remotefiles, "remoteFinalFileName", lambda src: "/dest/a.ts")
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "mv failed")

    result = remotefiles.moveTVFiles(["/src/a.ts"], "/dest")

    assert result is False


def test_moveTVFiles_size_mismatch_returns_false(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)

    monkeypatch.setattr(remotefiles, "remoteExists", lambda destdir, isdir=False: False)
    monkeypatch.setattr(remotefiles, "remoteMkdir", lambda destdir: True)

    sizes = {
        "/src/a.ts": 100,
        "/dest/a.ts": 90,
    }
    monkeypatch.setattr(remotefiles, "remoteFileSize", lambda fn: sizes[fn])
    monkeypatch.setattr(remotefiles, "remoteFinalFileName", lambda src: "/dest/a.ts")
    monkeypatch.setattr(remotefiles, "remoteCommand", lambda cmd, banner=False: "")

    result = remotefiles.moveTVFiles(["/src/a.ts"], "/dest")

    assert result is False


def test_moveTVFiles_success(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"mv_cmds": []}

    monkeypatch.setattr(remotefiles, "remoteExists", lambda destdir, isdir=False: False)
    monkeypatch.setattr(remotefiles, "remoteMkdir", lambda destdir: True)

    final_names = {
        "/dest/a.ts": "/dest/a.ts",
        "/dest/b.ts": "/dest/b.ts",
    }

    def fake_remoteFinalFileName(src):
        return final_names[src]

    sizes = {
        "/src/a.ts": 111,
        "/src/b.ts": 222,
        "/dest/a.ts": 111,
        "/dest/b.ts": 222,
    }

    def fake_remoteFileSize(fn):
        return sizes[fn]

    def fake_remoteCommand(cmd, banner=False):
        calls["mv_cmds"].append((cmd, banner))
        return ""

    monkeypatch.setattr(remotefiles, "remoteFinalFileName", fake_remoteFinalFileName)
    monkeypatch.setattr(remotefiles, "remoteFileSize", fake_remoteFileSize)
    monkeypatch.setattr(remotefiles, "remoteCommand", fake_remoteCommand)

    result = remotefiles.moveTVFiles(["/src/a.ts", "/src/b.ts"], "/dest", banner=True)

    assert result is True
    assert calls["mv_cmds"] == [
        ('mv "/src/a.ts" "/dest/a.ts"', True),
        ('mv "/src/b.ts" "/dest/b.ts"', True),
    ]


def test_moveTVFiles_exception_calls_errorNotify(monkeypatch):
    remotefiles = _load_remotefiles(monkeypatch)
    calls = {"count": 0}

    def boom(destdir, isdir=False):
        raise RuntimeError("probe failed")

    def fake_notify(exci, e):
        calls["count"] += 1
        calls["exc"] = exci
        calls["err"] = e

    monkeypatch.setattr(remotefiles, "remoteExists", boom)
    monkeypatch.setattr(remotefiles, "errorNotify", fake_notify)

    result = remotefiles.moveTVFiles(["/src/a.ts"], "/dest")

    assert result is False
    assert calls["count"] == 1
    assert isinstance(calls["err"], RuntimeError)