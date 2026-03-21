from dataclasses import dataclass
from .error_definition import ErrorDefinition
from zonc.location_file import Span

@dataclass
class Diagnostic:
    error_definition: ErrorDefinition
    args: dict[str, str] | None
    span_code: list[Span]
    span_errors: list[tuple[Span, str] | None]
    name_file: str