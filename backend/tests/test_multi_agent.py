"""
Unit tests for PRIV Multi-Agent Systems
"""

import pytest
import asyncio
from backend.multi_agent.dynamic_threat_detector import DynamicThreatDetector
from backend.multi_agent.priv_ai_ops_agent import PrivAIOpsAgent


@pytest.fixture
def threat_detector():
    """Create threat detector instance"""
    return DynamicThreatDetector()


@pytest.fixture
async def ai_ops_agent():
    """Create AI ops agent instance"""
    from backend.multi_agent.priv_agent_protocol import AgentType
    from unittest.mock import MagicMock
    agent = PrivAIOpsAgent(
        agent_id="test-aiops-001",
        agent_type=AgentType.AI_OPS,
        message_broker=MagicMock(),
        broker=MagicMock(),
        persona={}
    )
    yield agent
    # Cleanup
    if hasattr(agent, 'stop'):
        await agent.stop()


@pytest.mark.asyncio
async def test_threat_detector_initialization(threat_detector):
    """Test threat detector initialization"""
    assert threat_detector is not None


@pytest.mark.asyncio
async def test_threat_detection(threat_detector):
    """Test threat detection"""
    threats = await threat_detector._detect_threats()
    
    assert isinstance(threats, list)
    # Threats may or may not be detected depending on random chance
    for threat in threats:
        assert "type" in threat
        assert "severity" in threat
        assert "timestamp" in threat


@pytest.mark.asyncio
async def test_threat_handling(threat_detector):
    """Test threat handling"""
    test_threat = {
        "type": "unauthorized_access",
        "severity": "medium",
        "source": "test",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # Should not raise exception
    await threat_detector._handle_threat(test_threat)


@pytest.mark.asyncio
async def test_critical_threat_handling(threat_detector):
    """Test critical threat handling"""
    critical_threat = {
        "type": "data_breach",
        "severity": "critical",
        "source": "external",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # Should handle critical threats appropriately
    await threat_detector._handle_threat(critical_threat)


@pytest.mark.asyncio
async def test_aiops_agent_initialization(ai_ops_agent):
    """Test AI ops agent initialization"""
    assert ai_ops_agent is not None
    assert ai_ops_agent.agent_id == "test-aiops-001"


@pytest.mark.asyncio
async def test_infrastructure_alert_handling(ai_ops_agent):
    """Test infrastructure alert handling"""
    await ai_ops_agent.handle_infrastructure_alert("high_cpu_usage", "WARNING")
    await ai_ops_agent.handle_infrastructure_alert("high_memory_usage", "CRITICAL")


@pytest.mark.asyncio
async def test_auto_healing_strategies(ai_ops_agent):
    """Test auto-healing strategies"""
    # Test different healing strategies
    await ai_ops_agent._attempt_auto_healing("high_cpu_usage")
    await ai_ops_agent._attempt_auto_healing("high_memory_usage")
    await ai_ops_agent._attempt_auto_healing("high_disk_usage")
    await ai_ops_agent._attempt_auto_healing("service_down")
    await ai_ops_agent._attempt_auto_healing("network_issue")


@pytest.mark.asyncio
async def test_heal_high_cpu(ai_ops_agent):
    """Test CPU healing"""
    await ai_ops_agent._heal_high_cpu()


@pytest.mark.asyncio
async def test_heal_high_memory(ai_ops_agent):
    """Test memory healing"""
    await ai_ops_agent._heal_high_memory()


@pytest.mark.asyncio
async def test_heal_high_disk(ai_ops_agent):
    """Test disk healing"""
    await ai_ops_agent._heal_high_disk()


@pytest.mark.asyncio
async def test_heal_service_down(ai_ops_agent):
    """Test service healing"""
    await ai_ops_agent._heal_service_down()


@pytest.mark.asyncio
async def test_heal_network_issue(ai_ops_agent):
    """Test network healing"""
    await ai_ops_agent._heal_network_issue()


@pytest.mark.asyncio
async def test_unknown_alert_type(ai_ops_agent):
    """Test handling of unknown alert type"""
    # Should not raise exception
    await ai_ops_agent._attempt_auto_healing("unknown_alert_type")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])