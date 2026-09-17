import importlib.util
import json
import sqlite3
import zipfile


def _module():
    spec = importlib.util.spec_from_file_location("operator_release_gate", "scripts/operator_release_gate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_backup_restore_and_secret_scan(tmp_path):
    module = _module()
    source = tmp_path / "capture.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE records (key TEXT, body TEXT, digest TEXT)")
        connection.execute("INSERT INTO records VALUES ('a','b','c')")
    result = module.backup_restore_verify(source, tmp_path / "backup.sqlite3", tmp_path / "restore.sqlite3")
    assert result["restore_verified"] and result["record_count"] == 1
    root = tmp_path / "root"
    (root / "src").mkdir(parents=True)
    (root / "src/safe.py").write_text("TOKEN = 'configured-from-env'", encoding="utf-8")
    assert module.scan_secrets(root) == []
    (root / "src/leak.py").write_text("private_key='abcdefghijklmnop'", encoding="utf-8")
    assert module.scan_secrets(root) == ["src/leak.py"]
    bundle = tmp_path / "clean.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("safe.txt", "configured from environment")
    assert module.scan_bundle_secrets(bundle) == []


def test_release_gate_requires_packaging_backup_rollback_and_operator(tmp_path, monkeypatch):
    module = _module()
    root = tmp_path / "root"
    for name in ("src", "api", "scripts"):
        (root / name).mkdir(parents=True)
    capture = tmp_path / "capture.sqlite3"
    with sqlite3.connect(capture) as connection:
        connection.execute("CREATE TABLE records (key TEXT, body TEXT, digest TEXT)")
    release = tmp_path / "release"
    release.mkdir()
    bundle = release / "source.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("README.md", "rollback")
    report = {"status": "PASS", "source_bundle": {"path": bundle.name, "sha256": module.sha256(bundle)},
              "build": {"offline_install": "PASS"}}
    report_path = release / "packaging.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["gate", "--root", str(root), "--capture-db", str(capture),
                        "--packaging-report", str(report_path), "--release-dir", str(release / "gate"),
                        "--operator", "operator-1", "--approval", "I_APPROVE_READ_ONLY_RELEASE"])
    monkeypatch.setattr(module, "worktree_is_clean", lambda root: True)
    assert module.main() == 0
    receipt = json.loads((release / "gate/human-release-receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "APPROVED_READ_ONLY"
    assert receipt["backup"]["restore_verified"]
