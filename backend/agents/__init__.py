from .atlas import AtlasAgent
from .cipher import CipherAgent
from .nova import NovaAgent
from .lexis import LexisAgent
from .oracle import OracleAgent
from .hermes import HermesAgent
from .echo import EchoAgent
from .darwin import DarwinAgent
from .pixel import PixelAgent
from .nexus import NexusAgent
from .forge import ForgeAgent
from .sage import SageAgent
from .vector import VectorAgent
from .chronos import ChronosAgent
from .politeia import PoliteiaAgent
from .educraft import EduCraftAgent
from models.schemas import AgentType

# Registro de agentes
AGENT_REGISTRY = {
    AgentType.ATLAS: AtlasAgent,
    AgentType.CIPHER: CipherAgent,
    AgentType.NOVA: NovaAgent,
    AgentType.LEXIS: LexisAgent,
    AgentType.ORACLE: OracleAgent,
    AgentType.HERMES: HermesAgent,
    AgentType.ECHO: EchoAgent,
    AgentType.DARWIN: DarwinAgent,
    AgentType.PIXEL: PixelAgent,
    AgentType.NEXUS: NexusAgent,
    AgentType.FORGE: ForgeAgent,
    AgentType.SAGE: SageAgent,
    AgentType.VECTOR: VectorAgent,
    AgentType.CHRONOS: ChronosAgent,
    AgentType.POLITEIA: PoliteiaAgent,
    AgentType.EDUCRAFT: EduCraftAgent,
}


def get_agent(agent_type: AgentType):
    """Obtiene la clase del agente por tipo."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if not agent_class:
        return AGENT_REGISTRY[AgentType.ATLAS]  # Fallback a ATLAS
    return agent_class
