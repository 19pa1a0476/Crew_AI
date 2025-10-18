from agno.agent import Agent
from a2a.types import AgentSkill, AgentCard, AgentCapabilities

def create_agent_card(agent: Agent, agent_endpoint: str = "https://hostname/") -> None:
    if not agent.name:
        raise ValueError("Agent must have a name")
    skill = AgentSkill(
        id=f"{agent.name}",
        name=f"{agent.name}",
        description=f"{agent.role} capability",
        tags=[tool.name for tool in (agent.tools or [])],
        examples=[],
        inputModes=["text"],
        outputModes=["text"],
    )
    card = AgentCard(
        name=agent.name,
        description=agent.role,
        version="1.0.0",
        url=agent_endpoint,
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        # authentication=AgentAuthentication(schemes=["public"]),
        skills=[skill],
    )
    # agent_cards[agent.name] = card
    return card

