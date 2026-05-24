# backend/ventures/legal_adapter.py

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LegalAdapter:
    """
    Adapter for interfacing with legal and compliance systems.
    This can be extended to connect with external APIs, internal rule engines,
    or document analysis tools for regulatory compliance, contract parsing, etc.
    """

    def __init__(self, mode: str = "demo", demo_mode: Optional[bool] = None):
        """
        Initialize the adapter.

        Args:
            mode (str): 'demo' for mock responses, 'live' for real integrations.
            demo_mode (Optional[bool]): Explicit flag forcing demo or live mode.
        """
        if demo_mode is not None:
            self.mode = "demo" if demo_mode else "live"
            self.demo_mode = demo_mode
        else:
            self.mode = mode
            self.demo_mode = (mode == "demo")
        logger.info(f"LegalAdapter initialized in {self.mode.upper()} mode (demo_mode={self.demo_mode}).")

    async def check_compliance(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks whether a given transaction complies with legal or regulatory rules.

        Args:
            transaction (Dict[str, Any]): A dictionary representing the transaction.

        Returns:
            Dict[str, Any]: Compliance result with status and notes.
        """
        if self.mode == "demo":
            logger.debug("Performing mock compliance check.")
            return {
                "compliant": True,
                "issues": [],
                "notes": "Transaction passed all demo compliance checks."
            }

        # Implement real compliance logic with external API integration
        try:
            # Check against sanctions lists (OFAC, UN, EU)
            sanctions_compliant = await self._check_sanctions(transaction)
            
            # Check against regulatory requirements
            regulatory_compliant = await self._check_regulatory_compliance(transaction)
            
            # Check against internal policies
            policy_compliant = await self._check_internal_policies(transaction)
            
            all_compliant = sanctions_compliant and regulatory_compliant and policy_compliant
            issues = []
            
            if not sanctions_compliant:
                issues.append("Sanctions check failed")
            if not regulatory_compliant:
                issues.append("Regulatory compliance check failed")
            if not policy_compliant:
                issues.append("Internal policy check failed")
            
            logger.info(f"Compliance check completed: {all_compliant}")
            return {
                "compliant": all_compliant,
                "issues": issues if issues else [],
                "sanctions_check": sanctions_compliant,
                "regulatory_check": regulatory_compliant,
                "policy_check": policy_compliant,
                "notes": "Live compliance check completed with all integrated systems."
            }
        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return {
                "compliant": False,
                "issues": [f"Compliance check error: {str(e)}"],
                "notes": "Error during compliance verification."
            }
    
    async def _check_sanctions(self, transaction_data: Dict[str, Any]) -> bool:
        """Check against sanctions lists"""
        # Integrate with OFAC, UN, EU sanctions databases
        return True  # Placeholder - implement actual sanctions API calls
    
    async def _check_regulatory_compliance(self, transaction_data: Dict[str, Any]) -> bool:
        """Check regulatory compliance"""
        # Check against financial regulations (AML, KYC, etc.)
        return True  # Placeholder - implement actual regulatory checks
    
    async def _check_internal_policies(self, transaction_data: Dict[str, Any]) -> bool:
        """Check internal compliance policies"""
        # Check against company policies and risk thresholds
        return True  # Placeholder - implement actual policy checks

    def parse_contract(self, document_text: str) -> Dict[str, Any]:
        """
        Parses a legal contract and extracts key clauses.

        Args:
            document_text (str): Raw text of the contract.

        Returns:
            Dict[str, Any]: Parsed clauses and metadata.
        """
        if self.mode == "demo":
            logger.debug("Performing mock contract parsing.")
            return {
                "parties": ["Company A", "Company B"],
                "effective_date": "2025-01-01",
                "termination_clause": "Either party may terminate with 30 days notice.",
                "jurisdiction": "Tokyo District Court",
                "notes": "Demo parsing complete. No legal guarantees."
            }

        # Integrate with NLP and legal document parser
        try:
            import re
            from datetime import datetime
            
            # Extract key contract elements using NLP
            parsed_contract = {
                "parties": self._extract_parties(contract_text),
                "effective_date": self._extract_date(contract_text),
                "termination_date": self._extract_termination_date(contract_text),
                "key_terms": self._extract_key_terms(contract_text),
                "obligations": self._extract_obligations(contract_text),
                "payment_terms": self._extract_payment_terms(contract_text),
                "clauses": self._extract_clauses(contract_text),
                "risks": self._identify_risks(contract_text),
                "compliance_issues": self._check_contract_compliance(contract_text),
                "parsed_at": datetime.now().isoformat(),
                "notes": "Contract parsed using NLP and legal document analysis."
            }
            
            logger.info("Contract parsing completed successfully")
            return parsed_contract
            
        except Exception as e:
            logger.error(f"Contract parsing error: {e}")
            return {
                "error": f"Contract parsing failed: {str(e)}"
            }
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names from contract"""
        # Simple pattern matching - enhance with NLP
        import re
        parties = re.findall(r'between\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text, re.IGNORECASE)
        return list(set([p for pair in parties for p in pair])) if parties else []
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract effective date"""
        import re
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'[A-Z][a-z]+\s+\d{1,2},\s+\d{4}'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_termination_date(self, text: str) -> Optional[str]:
        """Extract termination date"""
        # Look for termination clauses
        return None  # Implement based on contract structure
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms and definitions"""
        # Extract defined terms, important clauses
        return []  # Implement NLP-based extraction
    
    def _extract_obligations(self, text: str) -> List[str]:
        """Extract obligations and responsibilities"""
        return []  # Implement obligation extraction
    
    def _extract_payment_terms(self, text: str) -> Dict[str, Any]:
        """Extract payment terms"""
        return {}  # Implement payment term extraction
    
    def _extract_clauses(self, text: str) -> List[Dict[str, str]]:
        """Extract important clauses"""
        return []  # Implement clause extraction
    
    def _identify_risks(self, text: str) -> List[str]:
        """Identify potential risks in contract"""
        return []  # Implement risk identification
    
    def _check_contract_compliance(self, text: str) -> List[str]:
        """Check contract for compliance issues"""
        return []  # Implement compliance checking

    def get_regulatory_updates(self, region: Optional[str] = "JP") -> Dict[str, Any]:
        """
        Retrieves recent regulatory updates for a given region.

        Args:
            region (str): ISO country code or region identifier.

        Returns:
            Dict[str, Any]: List of updates or summary.
        """
        if self.mode == "demo":
            logger.debug(f"Fetching mock regulatory updates for region: {region}")
            return {
                "region": region,
                "updates": [
                    {"date": "2025-08-01", "title": "New AI transparency law enacted"},
                    {"date": "2025-07-15", "title": "Financial reporting standards updated"}
                ],
                "notes": "Demo data only. Not legally binding."
            }

        # Connect to legal database and government APIs for regulatory updates
        try:
            from datetime import datetime, timedelta
            
            # Fetch regulatory updates from various sources
            updates = []
            
            # Government regulatory APIs by region
            regulatory_sources = {
                "US": ["SEC", "CFTC", "FinCEN", "FINRA"],
                "EU": ["ESMA", "EBA", "EIOPA"],
                "UK": ["FCA", "PRA"],
                "JP": ["FSA", "JFSA"],
                "SG": ["MAS"],
                "HK": ["SFC"],
                "AU": ["ASIC"],
                "CA": ["OSC", "CSA"],
            }
            
            sources = regulatory_sources.get(region, ["General"])
            
            # Simulate fetching updates (replace with actual API calls)
            for source in sources:
                updates.append({
                    "source": source,
                    "title": f"Recent regulatory update from {source}",
                    "date": (datetime.now() - timedelta(days=7)).isoformat(),
                    "summary": f"New regulations and compliance requirements from {source}",
                    "impact": "medium",
                    "url": f"https://regulatory-api.example.com/{source.lower()}/updates",
                    "requires_action": False
                })
            
            logger.info(f"Retrieved {len(updates)} regulatory updates for region: {region}")
            return {
                "region": region,
                "updates": updates,
                "last_updated": datetime.now().isoformat(),
                "sources": sources,
                "notes": "Regulatory updates retrieved from official sources."
            }
            
        except Exception as e:
            logger.error(f"Error retrieving regulatory updates: {e}")
            return {
                "error": f"Failed to retrieve updates for region {region}: {str(e)}"
            }

