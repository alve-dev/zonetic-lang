from .error_code import ErrorCode
from .severity import Severity

def zonny_clean(text: str):
    lines = text.splitlines()
    if lines and not lines[0].strip():
        lines.pop(0)
    if lines and not lines[-1].strip():
        lines.pop()
        
    if not lines: return ""

    first_line = lines[0]
    indent_to_remove = len(first_line) - len(first_line.lstrip())
 
    return "\n".join(line[indent_to_remove:] for line in lines)


class ErrorDefinition:
    def __init__(
        self,
        error_code: ErrorCode,
        severity: Severity,  
        message: str, 
        note: str,
        zonny: str,
    ):
        self.error_code = error_code
        self.severity = severity
        self.message = message
        self.note = note
        self.zonny = zonny_clean(zonny)