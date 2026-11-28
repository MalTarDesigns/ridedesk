"""The core reads verticals as data. It must never name one in code."""

import ast
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "ridedesk"
VERTICALS = Path(__file__).resolve().parent.parent / "verticals"


def names_in(source: str) -> list[str]:
    """Every identifier and string the code spells out, from its syntax tree."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        match node:
            case ast.Name(id=name) | ast.Attribute(attr=name) | ast.arg(arg=name):
                found.append(name)
            case (
                ast.FunctionDef(name=name)
                | ast.AsyncFunctionDef(name=name)
                | ast.ClassDef(name=name)
            ):
                found.append(name)
            case ast.keyword(arg=str() as name) | ast.alias(name=name):
                found.append(name)
            case ast.ImportFrom(module=str() as name) | ast.MatchAs(name=str() as name):
                found.append(name)
            case ast.Constant(value=str() | bytes() as value):
                found.append(value.decode() if isinstance(value, bytes) else value)
    return found


def violations(source: str, verticals: set[str]) -> list[str]:
    pattern = re.compile(
        r"(?<![a-z0-9])(" + "|".join(map(re.escape, verticals)) + r")(?![a-z0-9])",
        re.IGNORECASE,
    )
    return sorted({m.group(1).lower() for text in names_in(source) for m in pattern.finditer(text)})


def test_the_check_catches_every_way_of_naming_a_vertical() -> None:
    vertical = {"car_service"}
    for source in [
        'PRICE = {"car_service": 1}',
        "config.car_service",
        "def car_service(): pass",
        "f(car_service=1)",
        "from verticals import car_service",
        'path = b"car_service.yaml"',
        "async def car_service(): pass",
        'KIND = "CAR_SERVICE"',
        "match x:\n    case car_service: pass",
    ]:
        assert violations(source, vertical) == ["car_service"], source


def test_the_check_matches_whole_names_only() -> None:
    assert violations('rate = "hourly"', {"hour"}) == []


def test_no_core_module_names_a_vertical() -> None:
    verticals = {path.stem for path in VERTICALS.glob("*.yaml")}
    assert verticals, "expected at least one verticals/*.yaml"

    problems = {
        str(path.relative_to(PACKAGE.parent)): found
        for path in sorted(PACKAGE.rglob("*.py"))
        if (found := violations(path.read_text(), verticals))
    }

    assert problems == {}
