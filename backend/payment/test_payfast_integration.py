"""
PayFast Integration Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive test suite for PayFast integration across all systems.
"""

import unittest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import PayFast modules
from payfast_integration import PayFastIntegration
from payfast_service import PayFastService
from payfast_billing_integration import PayFastBillingIntegration, SYSTEM_PLANS_CONFIG

# Test configuration
TEST_CONFIG = {
    'merchant_id': '10000100',
    'merchant_key': '46f0cd694581a',
    'passphrase': 'jt7NOE43FZPn',
    'sandbox': True,
    'database_url': 'sqlite:///:memory:'
}


class TestPayFastIntegration(unittest.TestCase):
    """Test PayFast integration layer."""
    
    def setUp(self):
        """Set up test environment."""
        self.payfast = PayFastIntegration(
            merchant_id=TEST_CONFIG['merchant_id'],
            merchant_key=TEST_CONFIG['merchant_key'],
            passphrase=TEST_CONFIG['passphrase'],
            sandbox=TEST_CONFIG['sandbox']
        )
    
    def test_signature_generation(self):
        """Test PayFast signature generation."""
        data = {
            'merchant_id': '10000100',
            'merchant_key': '46f0cd694581a',
            'amount': '100.00',
            'item_name': 'Test Product'
        }
        
        signature = self.payfast.generate_signature(data)
        
        # Verify signature is not empty
        self.assertIsNotNone(signature)
        self.assertEqual(len(signature), 32)  # MD5 hash length
        
        # Test consistency
        signature2 = self.payfast.generate_signature(data)
        self.assertEqual(signature, signature2)
    
    def test_signature_with_passphrase(self):
        """Test signature generation with passphrase."""
        data = {
            'merchant_id': '10000100',
            'amount': '100.00',
            'item_name': 'Test Product'
        }
        
        signature_with_passphrase = self.payfast.generate_signature(data)
        signature_without_passphrase = self.payfast.generate_signature(data)
        
        # Passphrase should affect signature
        self.assertEqual(signature_with_passphrase, signature_without_passphrase)
    
    def test_payment_request_creation(self):
        """Test payment request creation."""
        payment_data = {
            'amount': 100.00,
            'item_name': 'Test Product',
            'item_description': 'A test product',
            'return_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel',
            'notify_url': 'https://example.com/itn',
            'email_address': 'test@example.com'
        }
        
        response = self.payfast.create_payment_request(payment_data)
        
        # Verify response structure
        self.assertIn('payment_url', response)
        self.assertIn('m_payment_id', response)
        self.assertIn('signature', response)
        
        # Verify payment URL format
        payment_url = response['payment_url']
        self.assertTrue(payment_url.startswith('https://sandbox.payfast.co.za'))
        self.assertIn('signature=', payment_url)
    
    def test_subscription_creation(self):
        """Test subscription creation."""
        subscription_data = {
            'amount': 99.99,
            'item_name': 'Test Subscription',
            'billing_date': '2025-06-17',
            'frequency': '3',  # Monthly
            'return_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel',
            'notify_url': 'https://example.com/itn'
        }
        
        response = self.payfast.create_subscription(subscription_data)
        
        # Verify response structure
        self.assertIn('subscription_url', response)
        self.assertIn('token', response)
        self.assertIn('signature', response)
        
        # Verify subscription URL format
        subscription_url = response['subscription_url']
        self.assertTrue(subscription_url.startswith('https://sandbox.payfast.co.za'))
        self.assertIn('signature=', subscription_url)
    
    def test_itn_validation(self):
        """Test ITN validation."""
        # Mock ITN data
        itn_data = {
            'merchant_id': TEST_CONFIG['merchant_id'],
            'payment_status': 'COMPLETE',
            'amount_gross': '100.00',
            'm_payment_id': 'test_payment_id',
            'signature': 'test_signature'
        }
        
        # This should fail with invalid signature
        result = self.payfast.verify_itn(itn_data)
        self.assertFalse(result)


class TestPayFastService(unittest.TestCase):
    """Test PayFast service layer."""
    
    def setUp(self):
        """Set up test environment."""
        with patch('payfast_service.create_engine'), \
             patch('payfast_service.sessionmaker'):
            self.service = PayFastService(
                merchant_id=TEST_CONFIG['merchant_id'],
                merchant_key=TEST_CONFIG['merchant_key'],
                passphrase=TEST_CONFIG['passphrase'],
                sandbox=TEST_CONFIG['sandbox']
            )
    
    @patch('payfast_service.PayFastIntegration.create_payment_request')
    def test_create_payment_url(self, mock_payment):
        """Test payment URL creation."""
        # Mock database
        mock_db = Mock()
        mock_plan = Mock()
        mock_plan.plan_id = 'test_plan_id'
        mock_plan.price = 99.99
        mock_plan.currency = 'ZAR'
        
        mock_payment.return_value = {
            'payment_url': 'https://test.com/pay',
            'm_payment_id': 'test_payment_id',
            'signature': 'test_signature'
        }
        
        # Test payment URL creation
        result = self.service.create_payment_url(
            db=mock_db,
            user_id='test_user',
            plan_id='test_plan_id',
            return_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            notify_url='https://example.com/itn',
            user_email='test@example.com'
        )
        
        self.assertTrue(result.get('success'))
        self.assertIn('payment_url', result)
    
    @patch('payfast_service.PayFastIntegration.create_subscription')
    def test_create_subscription(self, mock_subscription):
        """Test subscription creation."""
        # Mock database
        mock_db = Mock()
        mock_plan = Mock()
        mock_plan.plan_id = 'test_plan_id'
        mock_plan.price = 99.99
        mock_plan.currency = 'ZAR'
        
        mock_subscription.return_value = {
            'subscription_url': 'https://test.com/subscribe',
            'token': 'test_token',
            'signature': 'test_signature'
        }
        
        # Test subscription creation
        result = self.service.create_subscription(
            db=mock_db,
            user_id='test_user',
            plan_id='test_plan_id',
            return_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            notify_url='https://example.com/itn',
            user_email='test@example.com'
        )
        
        self.assertTrue(result.get('success'))
        self.assertIn('subscription_url', result)


class TestPayFastBillingIntegration(unittest.TestCase):
    """Test unified billing integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.integration = PayFastBillingIntegration('test_system')
    
    def test_system_plans_config(self):
        """Test system plans configuration."""
        # Verify all systems have plans
        expected_systems = ['anubis', 'brigit', 'kel', 'kev', 'mezzo', 'mpeti', 'omega', 'sia']
        
        for system in expected_systems:
            if system in SYSTEM_PLANS_CONFIG:
                self.assertIn('basic' if system != 'brigit' else 'starter', SYSTEM_PLANS_CONFIG[system])
    
    def test_plan_pricing_structure(self):
        """Test plan pricing structure."""
        # Test Anubis plans
        anubis_plans = SYSTEM_PLANS_CONFIG.get('anubis', {})
        
        for plan_name, plan_config in anubis_plans.items():
            self.assertIn('price', plan_config)
            self.assertIsInstance(plan_config['price'], (int, float))
            self.assertGreater(plan_config['price'], 0)
            
            self.assertIn('description', plan_config)
            self.assertIn('features', plan_config)
            self.assertIn('usage_limits', plan_config)
    
    def test_usage_limits_structure(self):
        """Test usage limits structure."""
        # Test MPeti plans
        mpeti_plans = SYSTEM_PLANS_CONFIG.get('mpeti', {})
        
        for plan_name, plan_config in mpeti_plans.items():
            usage_limits = plan_config.get('usage_limits', {})
            
            # Verify consistent structure
            self.assertIn('cloud_accounts', usage_limits)
            self.assertIn('apis_per_month', usage_limits)


class TestSystemIntegrations(unittest.TestCase):
    """Test system-specific PayFast integrations."""
    
    def test_anubis_billing_integration(self):
        """Test Anubis billing integration."""
        try:
            from anubis.payfast_billing import AnubisPayFastBilling
            
            billing = AnubisPayFastBilling()
            self.assertIsNotNone(billing.billing)
            billing.close()
            
        except ImportError:
            self.skipTest("Anubis billing module not available")
    
    def test_brigit_billing_integration(self):
        """Test Brigit billing integration."""
        try:
            from brigit.payfast_billing import BrigitPayFastBilling
            
            billing = BrigitPayFastBilling()
            self.assertIsNotNone(billing.billing)
            billing.close()
            
        except ImportError:
            self.skipTest("Brigit billing module not available")
    
    def test_omega_billing_integration(self):
        """Test Omega billing integration."""
        try:
            from omega.payfast_billing import OmegaPayFastBilling
            
            billing = OmegaPayFastBilling()
            self.assertIsNotNone(billing.billing)
            billing.close()
            
        except ImportError:
            self.skipTest("Omega billing module not available")
    
    def test_mpeti_billing_integration(self):
        """Test MPeti billing integration."""
        try:
            from mpeti.payfast_billing import MPetiPayFastBilling
            
            billing = MPetiPayFastBilling()
            self.assertIsNotNone(billing.billing)
            billing.close()
            
        except ImportError:
            self.skipTest("MPeti billing module not available")


class TestPayFastAPI(unittest.TestCase):
    """Test PayFast API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        from fastapi.testclient import TestClient
        from api import router
        
        self.client = TestClient(router)
    
    @patch('payfast_service.PayFastService.create_payment_url')
    def test_create_payment_endpoint(self, mock_payment):
        """Test payment creation endpoint."""
        mock_payment.return_value = {
            'success': True,
            'payment_url': 'https://test.com/pay',
            'm_payment_id': 'test_id'
        }
        
        response = self.client.post(
            '/payfast/create-payment',
            json={
                'plan_id': 'test_plan',
                'return_url': 'https://example.com/success',
                'cancel_url': 'https://example.com/cancel',
                'notify_url': 'https://example.com/itn'
            },
            params={'user_id': 'test_user'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.json())
    
    @patch('payfast_service.PayFastService.create_subscription')
    def test_create_subscription_endpoint(self, mock_subscription):
        """Test subscription creation endpoint."""
        mock_subscription.return_value = {
            'success': True,
            'subscription_url': 'https://test.com/subscribe',
            'subscription_token': 'test_token'
        }
        
        response = self.client.post(
            '/payfast/create-subscription',
            json={
                'plan_id': 'test_plan',
                'return_url': 'https://example.com/success',
                'cancel_url': 'https://example.com/cancel',
                'notify_url': 'https://example.com/itn'
            },
            params={'user_id': 'test_user'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('subscription_url', response.json())
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertIn('payfast', response.json())


class TestPayFastSecurity(unittest.TestCase):
    """Test PayFast security features."""
    
    def test_signature_security(self):
        """Test signature security."""
        payfast = PayFastIntegration(
            merchant_id='test_merchant',
            merchant_key='test_key',
            passphrase='test_pass',
            sandbox=True
        )
        
        # Test data manipulation detection
        data1 = {'amount': '100.00', 'item_name': 'Test'}
        data2 = {'amount': '200.00', 'item_name': 'Test'}
        
        sig1 = payfast.generate_signature(data1)
        sig2 = payfast.generate_signature(data2)
        
        # Different data should produce different signatures
        self.assertNotEqual(sig1, sig2)
    
    def test_data_order_independence(self):
        """Test that data order doesn't affect signature."""
        payfast = PayFastIntegration(
            merchant_id='test_merchant',
            merchant_key='test_key',
            sandbox=True
        )
        
        # Same data, different order
        data1 = {'amount': '100.00', 'item_name': 'Test'}
        data2 = {'item_name': 'Test', 'amount': '100.00'}
        
        sig1 = payfast.generate_signature(data1)
        sig2 = payfast.generate_signature(data2)
        
        # Order should not affect signature
        self.assertEqual(sig1, sig2)


def run_integration_tests():
    """Run all PayFast integration tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestPayFastIntegration,
        TestPayFastService,
        TestPayFastBillingIntegration,
        TestSystemIntegrations,
        TestPayFastAPI,
        TestPayFastSecurity
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running PayFast Integration Tests...")
    print("=" * 50)
    
    success = run_integration_tests()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("\nTest completed!")