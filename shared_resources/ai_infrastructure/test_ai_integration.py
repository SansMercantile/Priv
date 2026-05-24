#!/usr/bin/env python3
"""
Test script for Unified AI Infrastructure Integration
Tests the complete system integration with OMEGA
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIInfrastructureTester:
    """Test suite for AI Infrastructure"""
    
    def __init__(self):
        self.test_results = []
        self.components = {}
        
    async def test_quantum_interface(self):
        """Test quantum interface"""
        try:
            from quantum_interface_simple import QuantumInterface
            quantum = QuantumInterface()
            result = await quantum.initialize()
            self.test_results.append(("Quantum Interface", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["quantum"] = quantum
            logger.info("✅ Quantum Interface test completed")
        except Exception as e:
            self.test_results.append(("Quantum Interface", f"FAIL: {str(e)}"))
            logger.error(f"❌ Quantum Interface test failed: {e}")
    
    async def test_neuromorphic_interface(self):
        """Test neuromorphic interface"""
        try:
            from neuromorphic_interface_simple import NeuromorphicInterface
            neuro = NeuromorphicInterface()
            result = await neuro.initialize()
            self.test_results.append(("Neuromorphic Interface", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["neuromorphic"] = neuro
            logger.info("✅ Neuromorphic Interface test completed")
        except Exception as e:
            self.test_results.append(("Neuromorphic Interface", f"FAIL: {str(e)}"))
            logger.error(f"❌ Neuromorphic Interface test failed: {e}")
    
    async def test_ai_accelerator_interface(self):
        """Test AI accelerator interface"""
        try:
            from ai_accelerator_interface_simple import AIAcceleratorInterface
            accelerator = AIAcceleratorInterface()
            result = await accelerator.initialize()
            self.test_results.append(("AI Accelerator Interface", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["accelerator"] = accelerator
            logger.info("✅ AI Accelerator Interface test completed")
        except Exception as e:
            self.test_results.append(("AI Accelerator Interface", f"FAIL: {str(e)}"))
            logger.error(f"❌ AI Accelerator Interface test failed: {e}")
    
    async def test_cloud_interface(self):
        """Test cloud interface"""
        try:
            from cloud_interface_simple import CloudInterface
            cloud = CloudInterface()
            result = await cloud.initialize()
            self.test_results.append(("Cloud Interface", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["cloud"] = cloud
            logger.info("✅ Cloud Interface test completed")
        except Exception as e:
            self.test_results.append(("Cloud Interface", f"FAIL: {str(e)}"))
            logger.error(f"❌ Cloud Interface test failed: {e}")
    
    async def test_unified_orchestrator(self):
        """Test unified orchestrator"""
        try:
            from unified_orchestrator_simple import UnifiedOrchestrator
            orchestrator = UnifiedOrchestrator()
            result = await orchestrator.initialize()
            self.test_results.append(("Unified Orchestrator", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["orchestrator"] = orchestrator
            logger.info("✅ Unified Orchestrator test completed")
        except Exception as e:
            self.test_results.append(("Unified Orchestrator", f"FAIL: {str(e)}"))
            logger.error(f"❌ Unified Orchestrator test failed: {e}")
    
    async def test_integration(self):
        """Test full integration"""
        try:
            from main_integration_simple import MainIntegration
            integration = MainIntegration()
            result = await integration.initialize()
            self.test_results.append(("Main Integration", "PASS" if result["status"] == "success" else "FAIL"))
            self.components["integration"] = integration
            logger.info("✅ Main Integration test completed")
        except Exception as e:
            self.test_results.append(("Main Integration", f"FAIL: {str(e)}"))
            logger.error(f"❌ Main Integration test failed: {e}")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting AI Infrastructure Integration Tests")
        logger.info("=" * 60)
        
        # Test individual components
        await self.test_quantum_interface()
        await self.test_neuromorphic_interface()
        await self.test_ai_accelerator_interface()
        await self.test_cloud_interface()
        await self.test_unified_orchestrator()
        await self.test_integration()
        
        # Print results
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result == "PASS" else "❌ FAIL"
            logger.info(f"{test_name:<30} {status}")
            if result == "PASS":
                passed += 1
            else:
                failed += 1
        
        logger.info("=" * 60)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        return passed, failed

async def main():
    """Main test function"""
    tester = AIInfrastructureTester()
    passed, failed = await tester.run_all_tests()
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! AI Infrastructure is ready for integration.")
        return 0
    else:
        logger.error(f"\n⚠️  {failed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)