from zonc.ast import ZonType
from zonc.location_file import Span

class Symbol:
    def __init__(
        self,
        mutability: bool,
        zontype: ZonType,
        is_empty: bool,
        decl_span: Span
    ):
        self.mutability = mutability
        self.zontype = zontype
        self.is_empty = is_empty
        self.decl_span = decl_span
        