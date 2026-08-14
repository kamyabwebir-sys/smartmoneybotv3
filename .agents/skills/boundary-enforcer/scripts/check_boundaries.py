from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

_LAYERS = ("core", "domain", "analytics", "application")
_NETWORK_MODULES = (
    "aiohttp",
    "boto3",
    "httpx",
    "requests",
    "socket",
    "urllib.request",
    "web3",
    "websockets",
)
_FILESYSTEM_MODULES = ("os", "pathlib", "shelve", "shutil", "sqlite3", "tempfile")
_PURE_LAYERS = frozenset({"core", "domain", "analytics"})
_FORBIDDEN_LAYER_IMPORTS = {
    "core": (
        "smart_money.adapters",
        "smart_money.analytics",
        "smart_money.application",
        "smart_money.discovery",
        "smart_money.domain",
        "smart_money.ingestion",
        "smart_money.reporting",
    ),
    "domain": (
        "smart_money.adapters",
        "smart_money.analytics",
        "smart_money.application",
        "smart_money.discovery",
        "smart_money.ingestion",
        "smart_money.reporting",
    ),
    "analytics": (
        "smart_money.adapters",
        "smart_money.application",
        "smart_money.discovery",
        "smart_money.reporting",
    ),
    "application": (),
}


@dataclass(frozen=True, slots=True, order=True)
class Violation:
    path: str
    line: int
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _matches(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes)


def _imported_modules(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if node.module is None:
        return ()
    if node.module == "urllib":
        return tuple(f"urllib.{alias.name}" for alias in node.names)
    return (node.module,)


def _scan_file(path: Path, root: Path, layer: str) -> tuple[Violation, ...]:
    relative = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except (OSError, UnicodeError, SyntaxError) as exc:
        return (Violation(relative, 1, f"boundary parse failure: {exc}"),)

    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for module in _imported_modules(node):
                if _matches(module, _NETWORK_MODULES):
                    violations.append(
                        Violation(
                            relative,
                            node.lineno,
                            f"network dependency forbidden in {layer}: {module}",
                        )
                    )
                if layer in _PURE_LAYERS and _matches(module, _FILESYSTEM_MODULES):
                    violations.append(
                        Violation(
                            relative,
                            node.lineno,
                            f"filesystem dependency forbidden in {layer}: {module}",
                        )
                    )
                if _matches(module, _FORBIDDEN_LAYER_IMPORTS[layer]):
                    violations.append(
                        Violation(
                            relative,
                            node.lineno,
                            f"layer dependency forbidden in {layer}: {module}",
                        )
                    )
        elif (
            layer in _PURE_LAYERS
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            violations.append(
                Violation(
                    relative,
                    node.lineno,
                    f"filesystem call forbidden in {layer}: open",
                )
            )
    return tuple(violations)


def check_boundaries(root: Path) -> tuple[Violation, ...]:
    source_root = root / "src" / "smart_money"
    violations: list[Violation] = []
    for layer in _LAYERS:
        layer_root = source_root / layer
        if not layer_root.is_dir():
            violations.append(
                Violation(
                    layer_root.relative_to(root).as_posix(),
                    1,
                    "required layer directory not found",
                )
            )
            continue
        for path in sorted(layer_root.rglob("*.py")):
            violations.extend(_scan_file(path, root, layer))
    return tuple(sorted(violations))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check smartmoneybotv3 deterministic layer boundaries."
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="repository root; defaults to the skill's containing repository",
    )
    root = parser.parse_args().root.resolve()
    violations = check_boundaries(root)
    if violations:
        for violation in violations:
            print(violation.render())
        print(f"boundary-enforcer: FAIL ({len(violations)} violations)")
        return 1

    checked_files = sum(
        1
        for layer in _LAYERS
        for _ in (root / "src" / "smart_money" / layer).rglob("*.py")
    )
    print(f"boundary-enforcer: PASS ({checked_files} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
