from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    SEARCHING = "searching"
    GENERATING = "generating"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentEvent:
    agent_name: str
    status: AgentStatus
    message: str
    data: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    content: str
    sources: list[dict]
    confidence: float
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, name: str, llm_provider):
        self.name = name
        self.llm_provider = llm_provider

    @abstractmethod
    async def execute(self, query: str, context: dict | None = None) -> AsyncGenerator[AgentEvent, None]:
        ...
