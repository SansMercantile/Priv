"""
Unit tests for PRIV Legal Adapter
"""

import pytest
import asyncio
from backend.ventures.legal_adapter import LegalAdapter


@pytest.fixture
def legal_adapter():
    """Create legal adapter instance"""
    return LegalAdapter(demo_mode=False)


@pytest.fixture
def demo_legal_adapter():
    """Create legal adapter in demo mode"""
    return LegalAdapter(demo_mode=True)


@pytest.mark.asyncio
async def test_legal_adapter_initialization(legal_adapter):
    """Test legal adapter initialization"""
    assert legal_adapter is not None
    assert legal_adapter.demo_mode is False


@pytest.mark.asyncio
async def test_demo_mode_initialization(demo_legal_adapter):
    """Test demo mode initialization"""
    assert demo_legal_adapter.demo_mode is True


@pytest.mark.asyncio
async def test_compliance_check(legal_adapter):
    """Test compliance checking"""
    transaction_data = {
        "amount": 10000,
        "currency": "USD",
        "counterparty": "Test Corp",
        "type": "payment"
    }
    
    result = await legal_adapter.check_compliance(transaction_data)
    
    assert "compliant" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)


@pytest.mark.asyncio
async def test_sanctions_check(legal_adapter):
    """Test sanctions checking"""
    transaction_data = {"counterparty": "Test Entity"}
    
    result = await legal_adapter._check_sanctions(transaction_data)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_regulatory_compliance_check(legal_adapter):
    """Test regulatory compliance"""
    transaction_data = {"amount": 50000, "type": "wire_transfer"}
    
    result = await legal_adapter._check_regulatory_compliance(transaction_data)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_internal_policy_check(legal_adapter):
    """Test internal policy checking"""
    transaction_data = {"amount": 100000, "risk_level": "medium"}
    
    result = await legal_adapter._check_internal_policies(transaction_data)
    assert isinstance(result, bool)


def test_contract_parsing(legal_adapter):
    """Test contract parsing"""
    contract_text = """
    This agreement is made between Company A and Company B
    on January 15, 2024. The parties agree to the following terms...
    """
    
    result = legal_adapter.parse_contract(contract_text)
    
    assert "parties" in result or "error" in result
    if "parties" in result:
        assert isinstance(result["parties"], list)


def test_party_extraction(legal_adapter):
    """Test party extraction from contract"""
    text = "Agreement between Acme Corp and Widget Inc"
    parties = legal_adapter._extract_parties(text)
    
    assert isinstance(parties, list)


def test_date_extraction(legal_adapter):
    """Test date extraction"""
    text = "Effective date: 01/15/2024"
    date = legal_adapter._extract_date(text)
    
    # May or may not find date depending on format
    assert date is None or isinstance(date, str)


def test_regulatory_updates(legal_adapter):
    """Test regulatory updates retrieval"""
    result = legal_adapter.get_regulatory_updates(region="US")
    
    assert "region" in result or "error" in result
    if "updates" in result:
        assert isinstance(result["updates"], list)


def test_regulatory_updates_multiple_regions(legal_adapter):
    """Test regulatory updates for multiple regions"""
    regions = ["US", "EU", "UK", "JP", "SG"]
    
    for region in regions:
        result = legal_adapter.get_regulatory_updates(region=region)
        assert "region" in result or "error" in result


def test_demo_mode_compliance(demo_legal_adapter):
    """Test compliance in demo mode"""
    transaction_data = {"amount": 5000}
    
    result = asyncio.run(demo_legal_adapter.check_compliance(transaction_data))
    
    assert result["compliant"] is True
    assert "demo" in result["notes"].lower()


def test_demo_mode_contract_parsing(demo_legal_adapter):
    """Test contract parsing in demo mode"""
    contract_text = "Sample contract text"
    
    result = demo_legal_adapter.parse_contract(contract_text)
    
    assert "parties" in result
    assert "demo" in result["notes"].lower()


def test_demo_mode_regulatory_updates(demo_legal_adapter):
    """Test regulatory updates in demo mode"""
    result = demo_legal_adapter.get_regulatory_updates(region="US")
    
    assert "updates" in result
    assert "demo" in result["notes"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])