import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import json
import numpy as np
from dataclasses import dataclass
from enum import Enum
import re

from shared_resources.ai_core.symbolic_reasoner import SymbolicReasoner
from shared_resources.ai_core.neural_encoder import NeuralEncoder
from shared_resources.ai_core.knowledge_graph import KnowledgeGraph
from shared_resources.ai_core.rule_engine import RuleEngine
from shared_resources.utils.personality_loader import get_personality_loader
from priv.backend.config import settings

logger = logging.getLogger(__name__)

class ReasoningType(str, Enum):
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"

class ConfidenceLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class ReasoningStep:
    step_id: str
    reasoning_type: ReasoningType
    premise: str
    conclusion: str
    confidence: float
    evidence: List[str]
    timestamp: datetime

@dataclass
class SymbolicFact:
    predicate: str
    arguments: List[str]
    confidence: float
    source: str
    timestamp: datetime

class NeurosymbolicEngine:
    """Advanced neurosymbolic AI engine combining neural networks with symbolic reasoning"""
    
    def __init__(self, system_name: str = "PRIV"):
        # Load personality for context-aware reasoning
        self.system_name = system_name
        self.personality_loader = get_personality_loader(system_name)
        
        # Core components
        self.neural_encoder = NeuralEncoder()
        self.symbolic_reasoner = SymbolicReasoner()
        self.knowledge_graph = KnowledgeGraph()
        self.rule_engine = RuleEngine()
        
        # Knowledge base
        self.facts = []
        self.rules = []
        self.concepts = {}
        
        # Reasoning history
        self.reasoning_history = []
        self.learned_patterns = {}
        
        # Initialize with financial domain knowledge
        self._initialize_financial_knowledge()
        
        # Log personality context
        if self.personality_loader.is_loaded:
            logger.info(f"🎭 Neurosymbolic Engine initialized with personality: {self.personality_loader.get_identity_context()}")
        else:
            logger.info("Neurosymbolic Engine initialized")
    
    def _initialize_financial_knowledge(self):
        """Initialize with financial domain knowledge"""
        
        # Financial rules
        financial_rules = [
            {
                "id": "risk_management_1",
                "premise": "IF volatility > 0.03 AND position_size > 0.02",
                "conclusion": "THEN reduce_position_size",
                "confidence": 0.9,
                "domain": "risk_management"
            },
            {
                "id": "trend_following_1", 
                "premise": "IF sma_20 > sma_50 AND price > sma_20 AND rsi < 70",
                "conclusion": "THEN bullish_signal",
                "confidence": 0.8,
                "domain": "technical_analysis"
            },
            {
                "id": "sentiment_contrarian_1",
                "premise": "IF sentiment_score < -0.8 AND oversold_conditions",
                "conclusion": "THEN potential_reversal",
                "confidence": 0.7,
                "domain": "sentiment_analysis"
            },
            {
                "id": "macro_correlation_1",
                "premise": "IF inflation_rate > 4 AND interest_rate_rising",
                "conclusion": "THEN currency_strength_usd",
                "confidence": 0.85,
                "domain": "macroeconomics"
            }
        ]
        
        for rule in financial_rules:
            self.rule_engine.add_rule(rule)
        
        # Financial concepts
        financial_concepts = {
            "bullish": {
                "indicators": ["price_rising", "volume_increasing", "positive_sentiment"],
                "confidence_threshold": 0.7
            },
            "bearish": {
                "indicators": ["price_falling", "volume_increasing", "negative_sentiment"],
                "confidence_threshold": 0.7
            },
            "oversold": {
                "indicators": ["rsi < 30", "stochastic < 20", "negative_sentiment"],
                "confidence_threshold": 0.6
            },
            "overbought": {
                "indicators": ["rsi > 70", "stochastic > 80", "excessive_optimism"],
                "confidence_threshold": 0.6
            }
        }
        
        self.concepts.update(financial_concepts)
    
    async def reason(
        self,
        query: str,
        market_data: Dict[str, Any],
        context: Any,
        mood: str = "neutral"
    ) -> Dict[str, Any]:
        """Main reasoning function combining neural and symbolic approaches"""
        
        try:
            # 1. Neural encoding of inputs
            neural_features = await self.neural_encoder.encode(
                text=query,
                numerical_data=market_data,
                context=context
            )
            
            # 2. Extract symbolic facts from neural features
            symbolic_facts = await self._extract_symbolic_facts(
                neural_features, market_data, context
            )
            
            # 3. Apply symbolic reasoning
            reasoning_steps = await self.symbolic_reasoner.reason(
                facts=symbolic_facts,
                rules=self.rule_engine.get_applicable_rules(symbolic_facts),
                query=query
            )
            
            # 4. Fusion of neural and symbolic results
            fused_result = await self._fuse_neural_symbolic(
                neural_features, reasoning_steps, mood
            )
            
            # 5. Generate explanations
            explanations = await self._generate_explanations(
                reasoning_steps, fused_result
            )
            
            # 6. Update knowledge base
            await self._update_knowledge_base(
                symbolic_facts, reasoning_steps, fused_result
            )
            
            result = {
                "reasoning_type": "neurosymbolic",
                "neural_features": neural_features,
                "symbolic_facts": [fact.__dict__ for fact in symbolic_facts],
                "reasoning_steps": [step.__dict__ for step in reasoning_steps],
                "conclusions": fused_result,
                "explanations": explanations,
                "confidence": self._calculate_overall_confidence(reasoning_steps),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.reasoning_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in neurosymbolic reasoning: {e}")
            return self._generate_fallback_reasoning(query, str(e))
    
    async def _extract_symbolic_facts(
        self,
        neural_features: Dict[str, Any],
        market_data: Dict[str, Any],
        context: Any
    ) -> List[SymbolicFact]:
        """Extract symbolic facts from neural features and market data"""
        
        facts = []
        timestamp = datetime.utcnow()
        
        # Extract facts from market data
        if 'price' in market_data:
            price = market_data['price']
            facts.append(SymbolicFact(
                predicate="current_price",
                arguments=[str(price)],
                confidence=1.0,
                source="market_data",
                timestamp=timestamp
            ))
        
        # Extract technical indicator facts
        if hasattr(context, 'market_regime'):
            facts.append(SymbolicFact(
                predicate="market_regime",
                arguments=[context.market_regime.value],
                confidence=0.9,
                source="technical_analysis",
                timestamp=timestamp
            ))
        
        if hasattr(context, 'volatility_level'):
            vol_level = "high" if context.volatility_level > 0.03 else "low"
            facts.append(SymbolicFact(
                predicate="volatility_level",
                arguments=[vol_level],
                confidence=0.85,
                source="volatility_analysis",
                timestamp=timestamp
            ))
        
        # Extract sentiment facts
        if hasattr(context, 'sentiment_score'):
            sentiment = "positive" if context.sentiment_score > 0.2 else "negative" if context.sentiment_score < -0.2 else "neutral"
            facts.append(SymbolicFact(
                predicate="market_sentiment",
                arguments=[sentiment],
                confidence=abs(context.sentiment_score),
                source="sentiment_analysis",
                timestamp=timestamp
            ))
        
        # Extract neural-derived facts
        neural_sentiment = neural_features.get('sentiment_embedding', {})
        if neural_sentiment:
            confidence = neural_sentiment.get('confidence', 0.5)
            if confidence > 0.6:
                sentiment_label = neural_sentiment.get('label', 'neutral')
                facts.append(SymbolicFact(
                    predicate="neural_sentiment",
                    arguments=[sentiment_label],
                    confidence=confidence,
                    source="neural_network",
                    timestamp=timestamp
                ))
        
        # Extract pattern facts
        patterns = neural_features.get('detected_patterns', [])
        for pattern in patterns:
            facts.append(SymbolicFact(
                predicate="pattern_detected",
                arguments=[pattern['name']],
                confidence=pattern.get('confidence', 0.5),
                source="pattern_recognition",
                timestamp=timestamp
            ))
        
        return facts
    
    async def _fuse_neural_symbolic(
        self,
        neural_features: Dict[str, Any],
        reasoning_steps: List[ReasoningStep],
        mood: str
    ) -> Dict[str, Any]:
        """Fuse neural and symbolic reasoning results"""
        
        # Extract conclusions from reasoning steps
        symbolic_conclusions = [step.conclusion for step in reasoning_steps]
        
        # Get neural predictions
        neural_predictions = neural_features.get('predictions', {})
        
        # Mood-based weighting
        mood_weights = {
            "confident": {"neural": 0.4, "symbolic": 0.6},
            "anxious": {"neural": 0.3, "symbolic": 0.7},
            "neutral": {"neural": 0.5, "symbolic": 0.5}
        }
        
        weights = mood_weights.get(mood, mood_weights["neutral"])
        
        # Fuse recommendations
        fused_recommendations = []
        
        # Process symbolic conclusions
        for conclusion in symbolic_conclusions:
            if "bullish" in conclusion.lower():
                fused_recommendations.append({
                    "action": "buy",
                    "confidence": 0.7 * weights["symbolic"],
                    "source": "symbolic_reasoning",
                    "reasoning": conclusion
                })
            elif "bearish" in conclusion.lower():
                fused_recommendations.append({
                    "action": "sell", 
                    "confidence": 0.7 * weights["symbolic"],
                    "source": "symbolic_reasoning",
                    "reasoning": conclusion
                })
            elif "reduce" in conclusion.lower():
                fused_recommendations.append({
                    "action": "reduce_position",
                    "confidence": 0.8 * weights["symbolic"],
                    "source": "risk_management",
                    "reasoning": conclusion
                })
        
        # Process neural predictions
        if neural_predictions:
            for prediction in neural_predictions.get('actions', []):
                fused_recommendations.append({
                    "action": prediction.get('action', 'hold'),
                    "confidence": prediction.get('confidence', 0.5) * weights["neural"],
                    "source": "neural_network",
                    "reasoning": prediction.get('reasoning', 'Neural network prediction')
                })
        
        # Aggregate and rank recommendations
        action_scores = {}
        for rec in fused_recommendations:
            action = rec['action']
            if action not in action_scores:
                action_scores[action] = {'total_confidence': 0, 'count': 0, 'sources': []}
            
            action_scores[action]['total_confidence'] += rec['confidence']
            action_scores[action]['count'] += 1
            action_scores[action]['sources'].append(rec['source'])
        
        # Calculate final recommendations
        final_recommendations = []
        for action, scores in action_scores.items():
            avg_confidence = scores['total_confidence'] / scores['count']
            final_recommendations.append({
                'action': action,
                'confidence': avg_confidence,
                'support_count': scores['count'],
                'sources': list(set(scores['sources']))
            })
        
        # Sort by confidence
        final_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "recommended_actions": final_recommendations[:3],  # Top 3 recommendations
            "fusion_weights": weights,
            "neural_contribution": weights["neural"],
            "symbolic_contribution": weights["symbolic"],
            "mood_adjustment": mood,
            "total_recommendations_considered": len(fused_recommendations)
        }
    
    async def _generate_explanations(
        self,
        reasoning_steps: List[ReasoningStep],
        fused_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate human-readable explanations"""
        
        explanations = {
            "step_by_step": [],
            "summary": "",
            "key_factors": [],
            "confidence_breakdown": {}
        }
        
        # Step-by-step explanations
        for i, step in enumerate(reasoning_steps):
            explanation = {
                "step": i + 1,
                "type": step.reasoning_type.value,
                "explanation": f"Based on {step.premise}, I concluded {step.conclusion}",
                "confidence": step.confidence,
                "evidence": step.evidence
            }
            explanations["step_by_step"].append(explanation)
        
        # Summary explanation
        top_action = fused_result.get("recommended_actions", [{}])[0]
        if top_action:
            explanations["summary"] = (
                f"My analysis suggests {top_action.get('action', 'holding')} "
                f"with {top_action.get('confidence', 0):.1%} confidence, "
                f"based on {len(reasoning_steps)} reasoning steps and "
                f"input from {len(top_action.get('sources', []))} different analysis methods."
            )
        
        # Key factors
        for step in reasoning_steps:
            if step.confidence > 0.7:
                explanations["key_factors"].append({
                    "factor": step.premise,
                    "impact": step.conclusion,
                    "confidence": step.confidence
                })
        
        # Confidence breakdown
        explanations["confidence_breakdown"] = {
            "high_confidence_steps": len([s for s in reasoning_steps if s.confidence > 0.8]),
            "medium_confidence_steps": len([s for s in reasoning_steps if 0.5 < s.confidence <= 0.8]),
            "low_confidence_steps": len([s for s in reasoning_steps if s.confidence <= 0.5]),
            "average_confidence": np.mean([s.confidence for s in reasoning_steps]) if reasoning_steps else 0
        }
        
        return explanations
    
    def _calculate_overall_confidence(self, reasoning_steps: List[ReasoningStep]) -> float:
        """Calculate overall confidence from reasoning steps"""
        if not reasoning_steps:
            return 0.5
        
        # Weighted average based on step confidence and evidence strength
        total_weight = 0
        weighted_confidence = 0
        
        for step in reasoning_steps:
            evidence_weight = len(step.evidence) * 0.1 + 1  # More evidence = higher weight
            weight = step.confidence * evidence_weight
            
            weighted_confidence += step.confidence * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    async def _update_knowledge_base(
        self,
        facts: List[SymbolicFact],
        reasoning_steps: List[ReasoningStep],
        result: Dict[str, Any]
    ):
        """Update knowledge base with new facts and learned patterns"""
        
        # Add new facts
        self.facts.extend(facts)
        
        # Learn new patterns from successful reasoning
        for step in reasoning_steps:
            if step.confidence > 0.8:
                pattern_key = f"{step.reasoning_type.value}_{step.premise}"
                if pattern_key not in self.learned_patterns:
                    self.learned_patterns[pattern_key] = {
                        "conclusion": step.conclusion,
                        "confidence": step.confidence,
                        "usage_count": 1,
                        "success_rate": 1.0
                    }
                else:
                    pattern = self.learned_patterns[pattern_key]
                    pattern["usage_count"] += 1
                    # Update confidence based on repeated success
                    pattern["confidence"] = (pattern["confidence"] + step.confidence) / 2
        
        # Prune old facts (keep only recent ones)
        if len(self.facts) > 1000:
            self.facts = sorted(self.facts, key=lambda f: f.timestamp, reverse=True)[:500]
        
        logger.debug(f"Knowledge base updated: {len(self.facts)} facts, {len(self.learned_patterns)} patterns")
    
    async def symbolic_reasoning(self, context: Any, query: str) -> str:
        """Perform pure symbolic reasoning for specific queries"""
        
        try:
            # Extract relevant facts for symbolic reasoning
            relevant_facts = []
            
            if hasattr(context, 'risk_factors'):
                for risk in context.risk_factors:
                    relevant_facts.append(f"risk_factor({risk})")
            
            if hasattr(context, 'opportunities'):
                for opp in context.opportunities:
                    relevant_facts.append(f"opportunity({opp})")
            
            if hasattr(context, 'market_regime'):
                relevant_facts.append(f"market_regime({context.market_regime.value})")
            
            # Apply logical rules
            conclusions = []
            
            # Risk management rules
            if any("high" in fact for fact in relevant_facts):
                conclusions.append("Recommend conservative approach due to elevated risk factors")
            
            # Opportunity rules
            if any("opportunity" in fact for fact in relevant_facts):
                conclusions.append("Consider capitalizing on identified opportunities with appropriate risk management")
            
            # Market regime rules
            if "volatile" in str(relevant_facts):
                conclusions.append("Implement volatility-adjusted position sizing")
            
            return ". ".join(conclusions) if conclusions else "No specific symbolic conclusions derived"
            
        except Exception as e:
            logger.error(f"Symbolic reasoning error: {e}")
            return f"Symbolic reasoning encountered an error: {str(e)}"
    
    def _generate_fallback_reasoning(self, query: str, error: str) -> Dict[str, Any]:
        """Generate fallback reasoning when main process fails"""
        return {
            "reasoning_type": "fallback",
            "error": error,
            "conclusions": {
                "recommended_actions": [{
                    "action": "hold",
                    "confidence": 0.3,
                    "source": "fallback_logic",
                    "reasoning": "Conservative approach due to analysis error"
                }]
            },
            "explanations": {
                "summary": f"Analysis failed for query: '{query}'. Recommending conservative approach.",
                "error_details": error
            },
            "confidence": 0.3,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of current knowledge base"""
        return {
            "total_facts": len(self.facts),
            "learned_patterns": len(self.learned_patterns),
            "reasoning_history_length": len(self.reasoning_history),
            "top_patterns": sorted(
                self.learned_patterns.items(),
                key=lambda x: x[1]["confidence"] * x[1]["usage_count"],
                reverse=True
            )[:5],
            "recent_facts": [f.__dict__ for f in self.facts[-5:]] if self.facts else []
        }