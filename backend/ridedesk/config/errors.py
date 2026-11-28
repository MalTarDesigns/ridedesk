from pydantic import ValidationError


class ConfigError(ValueError):
    """A business config that failed validation, with every problem by path."""

    def __init__(self, source: str, problems: list[str]) -> None:
        self.source = source
        self.problems = problems
        super().__init__(f"{source}: " + "; ".join(problems))

    @classmethod
    def from_validation(cls, source: str, error: ValidationError) -> "ConfigError":
        return cls(source, [format_problem(item["loc"], item["msg"]) for item in error.errors()])


def format_problem(path: tuple[str | int, ...], message: str) -> str:
    dotted = ".".join(str(part) for part in path)
    return f"{dotted}: {message}" if dotted else message
