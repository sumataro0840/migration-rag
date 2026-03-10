from typing import List, Optional
from pydantic import BaseModel


class ColumnSpec(BaseModel):
    name: str
    type: str
    length: Optional[int] = None
    nullable: bool = False
    comment: Optional[str] = None


class ParsedRequest(BaseModel):
    table: str
    operation: str
    columns: List[ColumnSpec]
    need_down: bool = True