# shared_resources/agi_core/knowledge_sharing_protocol.py

from dataclasses import dataclass, field
from typing import Dict, Any, List
import uuid
import time

@dataclass
class KnowledgePacket:
    """
    A standardized data structure for sharing information between AGI agents.
    Ensures that all communication is structured, verifiable, and consistent.
    """
    source_agent_id: str
    target_agent_id: str # Can be 'broadcast' for all agents
    content_type: str  # e.g., 'market_insight', 'risk_assessment', 'trade_signal'
    content: Dict[str, Any]
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    priority: int = 1  # 1 (low) to 5 (critical)
    metadata: Dict[str, Any] = field(default_factory=dict)

class KnowledgeSharingProtocol:
    """
    Manages the encoding, decoding, and routing of KnowledgePackets.
    This acts as the communication bus for the entire AGI system, ensuring
    that agents can share insights and data effectively.
    """
    def __init__(self):
        self.message_queue: List[KnowledgePacket] = []
        self.agent_registry: Dict[str, Any] = {} # Simulates a registry of active agents
        print("KnowledgeSharingProtocol initialized.")

    def register_agent(self, agent_id: str, agent_instance: Any):
        """Registers an agent to receive targeted messages."""
        print(f"Registering agent: {agent_id}")
        self.agent_registry[agent_id] = agent_instance

    def create_packet(self, source_agent_id: str, target_agent_id: str, content_type: str, content: Dict[str, Any], priority: int = 1) -> KnowledgePacket:
        """
        Creates a new KnowledgePacket.

        Args:
            source_agent_id (str): The ID of the agent sending the packet.
            target_agent_id (str): The ID of the recipient agent or 'broadcast'.
            content_type (str): The type of information being sent.
            content (Dict[str, Any]): The actual data payload.
            priority (int): The priority of the message.

        Returns:
            KnowledgePacket: The newly created packet.
        """
        packet = KnowledgePacket(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content_type=content_type,
            content=content,
            priority=priority
        )
        return packet

    def broadcast(self, packet: KnowledgePacket):
        """
        Adds a packet to the central message queue for processing.
        In a real system, this would push to a message broker like RabbitMQ or Kafka.
        """
        print(f"Broadcasting packet {packet.packet_id} from {packet.source_agent_id} of type '{packet.content_type}'.")
        self.message_queue.append(packet)

    def get_messages_for_agent(self, agent_id: str) -> List[KnowledgePacket]:
        """
        Retrieves all broadcast or targeted messages for a specific agent.

        Args:
            agent_id (str): The ID of the agent fetching messages.

        Returns:
            List[KnowledgePacket]: A list of relevant packets.
        """
        relevant_packets = []
        remaining_packets = []
        for packet in self.message_queue:
            if packet.target_agent_id == agent_id or packet.target_agent_id == 'broadcast':
                relevant_packets.append(packet)
            else:
                remaining_packets.append(packet)
        
        # Consume the messages from the queue
        self.message_queue = remaining_packets
        return relevant_packets

# Example Usage:
if __name__ == '__main__':
    ksp = KnowledgeSharingProtocol()

    # Simulate agents
    class MockAgent:
        def __init__(self, agent_id):
            self.id = agent_id
        def receive(self, messages):
            print(f"\nAgent {self.id} received {len(messages)} message(s):")
            for msg in messages:
                print(f"  - From {msg.source_agent_id}: {msg.content}")

    sentiment_agent = MockAgent("SentimentAgent-01")
    risk_agent = MockAgent("RiskAgent-01")
    ksp.register_agent(sentiment_agent.id, sentiment_agent)
    ksp.register_agent(risk_agent.id, risk_agent)

    # 1. Sentiment agent detects a market shift and broadcasts it.
    sentiment_insight = {
        "symbol": "BTC/USD",
        "sentiment_score": 0.85,
        "summary": "Extremely bullish sentiment detected on social media."
    }
    packet1 = ksp.create_packet(
        source_agent_id=sentiment_agent.id,
        target_agent_id='broadcast',
        content_type='market_insight',
        content=sentiment_insight,
        priority=4
    )
    ksp.broadcast(packet1)

    # 2. Risk agent fetches messages from the protocol.
    risk_agent_messages = ksp.get_messages_for_agent(risk_agent.id)
    risk_agent.receive(risk_agent_messages)
    
    # 3. Risk agent sends a targeted warning back to the sentiment agent.
    risk_warning = {
        "warning": "High sentiment correlation detected. This pattern has preceded flash crashes. Advise caution."
    }
    packet2 = ksp.create_packet(
        source_agent_id=risk_agent.id,
        target_agent_id=sentiment_agent.id,
        content_type='risk_assessment',
        content=risk_warning,
        priority=5
    )
    ksp.broadcast(packet2)
    
    # 4. Sentiment agent checks its "mailbox".
    sentiment_agent_messages = ksp.get_messages_for_agent(sentiment_agent.id)
    sentiment_agent.receive(sentiment_agent_messages)
    
    print(f"\nFinal message queue size: {len(ksp.message_queue)}")
