from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class AgentType(str, Enum):
    ATLAS = "atlas"
    CIPHER = "cipher"
    NOVA = "nova"
    LEXIS = "lexis"
    ORACLE = "oracle"
    HERMES = "hermes"
    ECHO = "echo"
    DARWIN = "darwin"
    PIXEL = "pixel"
    NEXUS = "nexus"
    FORGE = "forge"
    SAGE = "sage"
    VECTOR = "vector"
    CHRONOS = "chronos"
    POLITEIA = "politeia"


class ModelTier(str, Enum):
    FREE_FAST = "free_fast"
    FREE_BALANCED = "free_balanced"
    FREE_DEEP = "free_deep"
    PAID_CRITICAL = "paid_critical"


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    message: str
    agent: AgentType = AgentType.ATLAS
    conversation_id: Optional[str] = None
    history: List[Message] = Field(default_factory=list)
    stream: bool = True
    model_tier: Optional[ModelTier] = None


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    content: str
    agent: AgentType
    model_used: str
    conversation_id: str
    tokens_used: Optional[int] = None


class AgentInfo(BaseModel):
    id: AgentType
    name: str
    description: str
    icon: str
    capabilities: List[str]
    preferred_model: str


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
