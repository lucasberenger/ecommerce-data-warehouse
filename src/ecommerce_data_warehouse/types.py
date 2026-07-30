from dataclasses import dataclass
from enum import Enum

class PipelineStatus(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

@dataclass(slots=True)
class PipelineRespose:
    table: str
    status: PipelineStatus
    rows: int