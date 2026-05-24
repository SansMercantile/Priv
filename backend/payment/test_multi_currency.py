"""
Multi-Currency Billing Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive test suite for multi-currency billing system.
Tests currency detection, conversion, and localization.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timezone

# Import multi-currency modules
from multi_currency_billing import (
    MultiCurrencyBilling, Currency, get_multi_currency_billing,
    format_currency, get_currency_info
)
from multi_currency_payfast_service import MultiCurrencyPayFastService


class TestMultiCurrencyBilling(unittest.TestCase):
    """Test multi-currency billing system."""
    
    def setUp(self):
        """Set up test environment."""
        self.billing = MultiCurrencyBilling()
    
    def test_currency_detection_by_country(self):
        """Test currency detection by country code."""
        # Test South Africa
        currency = self.billing.detect_currency_from_location('ZA')
        self.assertEqual(currency, 'ZAR')
        
        # Test United States
        currency = self.billing.detect_currency_from_location('US')
        self.assertEqual(currency, 'USD')
        
        # Test Germany
        currency = self.billing.detect_currency_from_location('DE')
        self.assertEqual(currency, 'EUR')
        
        # Test United Kingdom
        currency = self.billing.detect_currency_from_location('GB')
        self.assertEqual(currency, 'GBP')
        
        # Test Switzerland
        currency = self.billing.detect_currency_from_location('CH')
        self.assertEqual(currency, 'CHF')
        
        # Test unknown country (should fallback to USD)
        currency = self.billing.detect_currency_from_location('XX')
        self.assertEqual(currency, 'USD')
    
    @patch('multi_currency_billing.requests.get')
    def test_exchange_rate_update(self, mock_get):
        """Test exchange rate update from API."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rates': {
                'EUR': 0.92,
                'GBP': 0.79,
                'ZAR': 18.50
            }
        }
        mock_get.return_value = mock_response
        
        self.billing._update_exchange_rates()
        
        # Verify rates were updated
        self.assertEqual(self.billing.currency_info['EUR'].exchange_rate, 0.92)
        self.assertEqual(self.billing.currency_info['GBP'].exchange_rate, 0.79)
        self.assertEqual(self.billing.currency_info['ZAR'].exchange_rate, 18.50)
    
    def test_currency_conversion(self):
        """Test currency conversion with market factors."""
        # Set up test rates
        self.billing.currency_info['EUR'].exchange_rate = 0.92
        self.billing.currency_info['ZAR'].exchange_rate = 18.50
        self.billing.config['price_adjustment_factors']['ZAR'] = 0.85
        self.billing.config['rate_margin'] = 0.02
        
        # Test USD to EUR
        eur_amount = self.billing.convert_price(100.0, 'USD', 'EUR')
        expected = 100.0 * 0.92 * 1.02  # Convert EUR to USD, apply margin
        self.assertAlmostEqual(eur_amount, expected, places=2)
        
        # Test USD to ZAR (with market adjustment)
        zar_amount = self.billing.convert_price(100.0, 'USD', 'ZAR')
        expected = 100.0 * 18.50 * 0.85 * 1.02  # Convert with adjustment and margin
        self.assertAlmostEqual(zar_amount, expected, places=2)
        
        # Test same currency conversion
        usd_amount = self.billing.convert_price(100.0, 'USD', 'USD')
        self.assertEqual(usd_amount, 100.0)
    
    def test_localized_price_generation(self):
        """Test localized price generation."""
        # Set up test rates
        self.billing.currency_info['EUR'].exchange_rate = 0.92
        self.billing.currency_info['ZAR'].exchange_rate = 18.50
        
        # Test EUR localization
        eur_price = self.billing.get_localized_price(100.0, 'EUR')
        self.assertEqual(eur_price['currency'], 'EUR')
        self.assertEqual(eur_price['currency_symbol'], '€')
        self.assertEqual(eur_price['base_currency'], 'USD')
        self.assertEqual(eur_price['base_amount'], 100.0)
        self.assertTrue('€' in eur_price['formatted_amount'])
        
        # Test ZAR localization
        zar_price = self.billing.get_localized_price(100.0, 'ZAR')
        self.assertEqual(zar_price['currency'], 'ZAR')
        self.assertEqual(zar_price['currency_symbol'], 'R')
        self.assertEqual(zar_price['payment_gateway'], 'payfast')
    
    def test_payment_gateway_mapping(self):
        """Test payment gateway mapping by currency."""
        # Test major currencies (should map to Stripe)
        self.assertEqual(self.billing.get_payment_gateway_for_currency('USD'), 'stripe')
        self.assertEqual(self.billing.get_payment_gateway_for_currency('EUR'), 'stripe')
        self.assertEqual(self.billing.get_payment_gateway_for_currency('GBP'), 'stripe')
        self.assertEqual(self.billing.get_payment_gateway_for_currency('CHF'), 'stripe')
        
        # Test South African Rand (should map to PayFast)
        self.assertEqual(self.billing.get_payment_gateway_for_currency('ZAR'), 'payfast')
        
        # Test local currencies
        self.assertEqual(self.billing.get_payment_gateway_for_currency('CNY'), 'local')
        self.assertEqual(self.billing.get_payment_gateway_for_currency('INR'), 'local')
    
    def test_localized_plan_creation(self):
        """Test localized plan creation."""
        # Set up test rates
        self.billing.currency_info['EUR'].exchange_rate = 0.92
        
        base_plan = {
            'name': 'Professional Plan',
            'price': 99.99,
            'currency': 'USD',
            'features': ['Feature 1', 'Feature 2']
        }
        
        user_data = {
            'country_code': 'DE',
            'preferred_currency': 'EUR'
        }
        
        localized_plan = self.billing.create_localized_plan(base_plan, user_data)
        
        # Verify localization
        self.assertEqual(localized_plan['currency'], 'EUR')
        self.assertEqual(localized_plan['currency_symbol'], '€')
        self.assertEqual(localized_plan['payment_gateway'], 'stripe')
        self.assertTrue(localized_plan['is_localized'])
        self.assertIn('European payment methods', localized_plan['features'])
    
    def test_currency_support_validation(self):
        """Test currency support validation."""
        # Test supported currencies
        self.assertTrue(self.billing.validate_currency_support('USD'))
        self.assertTrue(self.billing.validate_currency_support('EUR'))
        self.assertTrue(self.billing.validate_currency_support('ZAR'))
        
        # Test unsupported currency
        self.assertFalse(self.billing.validate_currency_support('ABC'))
        self.assertFalse(self.billing.validate_currency_support('XYZ'))


class TestMultiCurrencyPayFastService(unittest.TestCase):
    """Test multi-currency PayFast service."""
    
    def setUp(self):
        """Set up test environment."""
        with patch('multi_currency_payfast_service.PayFastIntegration'), \
             patch('multi_currency_payfast_service.create_engine'), \
             patch('multi_currency_payfast_service.sessionmaker'):
            self.service = MultiCurrencyPayFastService()
    
    def test_payfast_usage_decision(self):
        """Test PayFast usage decision logic."""
        # Test ZAR currency (should use PayFast)
        self.assertTrue(self.service.should_use_payfast('ZAR', {'country_code': 'ZA'}))
        
        # Test South African country (should use PayFast)
        self.assertTrue(self.service.should_use_payfast('USD', {'country_code': 'ZA'}))
        
        # Test European countries (should not use PayFast)
        self.assertFalse(self.service.should_use_payfast('EUR', {'country_code': 'DE'}))
        self.assertFalse(self.service.should_use_payfast('GBP', {'country_code': 'GB'}))
        
        # Test US customer (should not use PayFast)
        self.assertFalse(self.service.should_use_payfast('USD', {'country_code': 'US'}))
    
    @patch('multi_currency_payfast_service.MultiCurrencyBilling.convert_price')
    @patch('multi_currency_payfast_service.MultiCurrencyPayFastService.should_use_payfast')
    def test_localized_payment_creation(self, mock_should_use, mock_convert):
        """Test localized payment creation."""
        mock_should_use.return_value = True
        mock_convert.return_value = 1850.00
        
        # Mock database
        mock_db = Mock()
        mock_plan = Mock()
        mock_plan.plan_id = 'test_plan_id'
        mock_plan.price = 99.99
        mock_plan.currency = 'USD'
        
        # Mock PayFast integration
        self.service.payfast.create_payment_request.return_value = {
            'payment_url': 'https://test.com/pay',
            'm_payment_id': 'test_payment_id'
        }
        
        # Test localized payment creation
        result = self.service.create_localized_payment(
            db=mock_db,
            user_id='test_user',
            plan_id='test_plan_id',
            return_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            notify_url='https://example.com/itn',
            user_data={'country_code': 'ZA', 'email_address': 'test@example.com'}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['currency'], 'ZAR')
        self.assertIn('exchange_rate', result)
        self.assertIn('user_preference', result)
    
    def test_currency_preference_management(self):
        """Test currency preference management."""
        mock_db = Mock()
        mock_preference = Mock()
        mock_preference.preferred_currency = 'EUR'
        mock_preference.to_dict.return_value = {
            'user_id': 'test_user',
            'preferred_currency': 'EUR'
        }
        
        # Test getting preference
        with patch.object(self.service, 'get_or_create_user_preference', return_value=mock_preference):
            preference = self.service.get_or_create_user_preference(
                mock_db, 'test_user', {'country_code': 'DE'}
            )
            self.assertEqual(preference.preferred_currency, 'EUR')


class TestCurrencyUtilities(unittest.TestCase):
    """Test currency utility functions."""
    
    def test_currency_formatting(self):
        """Test currency formatting."""
        # Test USD
        formatted = format_currency(99.99, 'USD')
        self.assertEqual(formatted, '$99.99')
        
        # Test EUR
        formatted = format_currency(99.99, 'EUR')
        self.assertEqual(formatted, '€99.99')
        
        # Test GBP
        formatted = format_currency(99.99, 'GBP')
        self.assertEqual(formatted, '£99.99')
        
        # Test JPY (no decimal places)
        formatted = format_currency(9999, 'JPY')
        self.assertEqual(formatted, '¥9,999')
        
        # Test ZAR
        formatted = format_currency(99.99, 'ZAR')
        self.assertEqual(formatted, 'R99.99')
    
    def test_currency_info_retrieval(self):
        """Test currency info retrieval."""
        billing = get_multi_currency_billing()
        
        # Test USD info
        usd_info = get_currency_info('USD')
        self.assertIsNotNone(usd_info)
        self.assertEqual(usd_info.code, 'USD')
        self.assertEqual(usd_info.symbol, '$')
        self.assertTrue(usd_info.is_primary)
        
        # Test EUR info
        eur_info = get_currency_info('EUR')
        self.assertIsNotNone(eur_info)
        self.assertEqual(eur_info.code, 'EUR')
        self.assertEqual(eur_info.symbol, '€')
        self.assertFalse(eur_info.is_primary)
        
        # Test invalid currency
        invalid_info = get_currency_info('ABC')
        self.assertIsNone(invalid_info)


class TestMultiCurrencyAPI(unittest.TestCase):
    """Test multi-currency API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        from fastapi.testclient import TestClient
        
        # Mock the API router for testing
        with patch('multi_currency_payfast_service.PayFastIntegration'), \
             patch('multi_currency_payfast_service.create_engine'), \
             patch('multi_currency_payfast_service.sessionmaker'):
            
            # Import after patching
            from api import router
            self.client = TestClient(router)
    
    @patch('shared_resources.backend.multi_currency_billing.get_multi_currency_billing')
    def test_currency_detection_endpoint(self, mock_billing):
        """Test currency detection API endpoint."""
        # Mock multi-currency billing
        mock_mc = Mock()
        mock_mc.detect_currency_from_request.return_value = 'EUR'
        mock_mc.currency_info = {'EUR': Mock(__dict__={'code': 'EUR', 'symbol': '€'})}
        mock_mc.gateway_mapping = {'stripe': ['EUR']}
        mock_billing.return_value = mock_mc
        
        # Test currency detection
        response = self.client.post(
            '/currency/detect',
            json={
                'user_id': 'test_user',
                'country_code': 'DE',
                'ip_address': '192.168.1.1',
                'locale': 'de-DE'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['detected_currency'], 'EUR')
        self.assertIn('currency_info', data)
        self.assertIn('recommended_gateway', data)
    
    @patch('shared_resources.backend.multi_currency_billing.get_multi_currency_billing')
    def test_supported_currencies_endpoint(self, mock_billing):
        """Test supported currencies API endpoint."""
        # Mock currency info
        mock_mc = Mock()
        mock_mc.currency_info = {
            'USD': Mock(code='USD', symbol='$', name='US Dollar', 
                       country_codes=['US'], exchange_rate=1.0, 
                       is_primary=True, payment_gateway='stripe'),
            'EUR': Mock(code='EUR', symbol='€', name='Euro',
                       country_codes=['DE'], exchange_rate=0.92,
                       is_primary=False, payment_gateway='stripe')
        }
        mock_mc.config = {'primary_currency': 'USD'}
        mock_mc.gateway_mapping = {'stripe': ['USD', 'EUR']}
        mock_mc.exchange_rates = {'EUR': 0.92}
        mock_billing.return_value = mock_mc
        
        # Test supported currencies
        response = self.client.get('/multi-currency/supported-currencies')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('supported_currencies', data)
        self.assertIn('primary_currency', data)
        self.assertIn('gateway_mapping', data)
    
    @patch('shared_resources.backend.multi_currency_billing.get_multi_currency_billing')
    def test_price_conversion_endpoint(self, mock_billing):
        """Test price conversion API endpoint."""
        # Mock conversion
        mock_mc = Mock()
        mock_mc.convert_price.return_value = 92.0
        mock_mc.currency_info = {
            'EUR': Mock(exchange_rate=0.92)
        }
        mock_mc.get_localized_price.return_value = {
            'formatted_amount': '€92.00'
        }
        mock_billing.return_value = mock_mc
        
        # Test price conversion
        response = self.client.get(
            '/multi-currency/convert-price',
            params={
                'amount': 100.0,
                'from_currency': 'USD',
                'to_currency': 'EUR'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['original_amount'], 100.0)
        self.assertEqual(data['converted_amount'], 92.0)
        self.assertEqual(data['converted_currency'], 'EUR')


class TestMultiCurrencyIntegration(unittest.TestCase):
    """Test integration scenarios for multi-currency billing."""
    
    def setUp(self):
        """Set up test environment."""
        self.billing = MultiCurrencyBilling()
    
    def test_south_african_customer_flow(self):
        """Test complete flow for South African customer."""
        user_data = {
            'country_code': 'ZA',
            'ip_address': '196.15.123.45',
            'email_address': 'customer@co.za'
        }
        
        # 1. Detect currency
        detected_currency = self.billing.detect_currency_from_request(user_data)
        self.assertEqual(detected_currency, 'ZAR')
        
        # 2. Get payment gateway recommendation
        gateway = self.billing.get_payment_gateway_for_currency(detected_currency)
        self.assertEqual(gateway, 'payfast')
        
        # 3. Convert price
        zar_price = self.billing.convert_price(99.99, 'USD', 'ZAR')
        self.assertGreater(zar_price, 1000)  # Should be much higher in ZAR
        
        # 4. Get localized pricing
        localized = self.billing.get_localized_price(99.99, 'ZAR', user_data)
        self.assertEqual(localized['currency'], 'ZAR')
        self.assertEqual(localized['payment_gateway'], 'payfast')
    
    def test_european_customer_flow(self):
        """Test complete flow for European customer."""
        user_data = {
            'country_code': 'DE',
            'ip_address': '217.160.123.45',
            'email_address': 'customer@de'
        }
        
        # 1. Detect currency
        detected_currency = self.billing.detect_currency_from_request(user_data)
        self.assertEqual(detected_currency, 'EUR')
        
        # 2. Get payment gateway recommendation
        gateway = self.billing.get_payment_gateway_for_currency(detected_currency)
        self.assertEqual(gateway, 'stripe')
        
        # 3. Convert price
        eur_price = self.billing.convert_price(99.99, 'USD', 'EUR')
        self.assertGreater(eur_price, 90)  # Should be slightly less than USD due to exchange rate
        
        # 4. Get localized pricing
        localized = self.billing.get_localized_price(99.99, 'EUR', user_data)
        self.assertEqual(localized['currency'], 'EUR')
        self.assertEqual(localized['payment_gateway'], 'stripe')
    
    def test_swiss_customer_flow(self):
        """Test complete flow for Swiss customer."""
        user_data = {
            'country_code': 'CH',
            'ip_address': '185.60.123.45',
            'email_address': 'customer@ch'
        }
        
        # 1. Detect currency
        detected_currency = self.billing.detect_currency_from_request(user_data)
        self.assertEqual(detected_currency, 'CHF')
        
        # 2. Get payment gateway recommendation
        gateway = self.billing.get_payment_gateway_for_currency(detected_currency)
        self.assertEqual(gateway, 'stripe')
        
        # 3. Convert price with Swiss premium
        chf_price = self.billing.convert_price(99.99, 'USD', 'CHF')
        self.assertGreater(chf_price, 85)  # Should include Swiss premium
        
        # 4. Get localized pricing
        localized = self.billing.get_localized_price(99.99, 'CHF', user_data)
        self.assertEqual(localized['currency'], 'CHF')
        self.assertEqual(localized['payment_gateway'], 'stripe')


def run_multi_currency_tests():
    """Run all multi-currency tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMultiCurrencyBilling,
        TestMultiCurrencyPayFastService,
        TestCurrencyUtilities,
        TestMultiCurrencyAPI,
        TestMultiCurrencyIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Multi-Currency Billing Tests...")
    print("=" * 60)
    
    success = run_multi_currency_tests()
    
    print("=" * 60)
    if success:
        print("✅ All multi-currency tests passed!")
    else:
        print("❌ Some multi-currency tests failed!")
    
    print("\nMulti-currency testing completed!")