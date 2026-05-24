"""
Multi-Currency Support Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This migration adds multi-currency support to the existing payment system.
Adds currency detection, conversion, and localization capabilities.
"""

-- Migration: Add Multi-Currency Support
-- Date: 2025-06-17
-- Description: Add multi-currency fields and user currency preferences

-- 1. Add multi-currency fields to existing tables
-- Add localized pricing support to plans table
ALTER TABLE plans 
ADD COLUMN IF NOT EXISTS localized_prices JSON,
ADD COLUMN IF NOT EXISTS supported_currencies JSON DEFAULT '["USD"]',
ADD COLUMN IF NOT EXISTS pricing_model VARCHAR(20) DEFAULT 'fixed',
ADD COLUMN IF NOT EXISTS geo_pricing_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS base_currency VARCHAR(3) DEFAULT 'USD';

-- Add multi-currency support to invoices table
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS exchange_rate DECIMAL(10,6),
ADD COLUMN IF NOT EXISTS base_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS localized_amount DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS payment_gateway VARCHAR(20) DEFAULT 'stripe',
ADD COLUMN IF NOT EXISTS tax_info JSON,
ADD COLUMN IF NOT EXISTS discount_info JSON;

-- Add currency to billing history
ALTER TABLE billing_history 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3);

-- 2. Create user currency preferences table
CREATE TABLE IF NOT EXISTS user_currency_preferences (
    preference_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    country_code VARCHAR(2),
    timezone VARCHAR(50),
    locale VARCHAR(10),
    auto_detect_currency BOOLEAN DEFAULT TRUE,
    payment_method_preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Create exchange rates table
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id VARCHAR(36) PRIMARY KEY,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(15,8) NOT NULL,
    provider VARCHAR(50) DEFAULT 'manual',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(from_currency, to_currency)
);

-- 4. Create currency conversion logs table
CREATE TABLE IF NOT EXISTS currency_conversion_logs (
    log_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255),
    from_amount DECIMAL(15,2) NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_amount DECIMAL(15,2) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,8) NOT NULL,
    adjustment_factor DECIMAL(5,4) DEFAULT 1.0,
    context VARCHAR(100), -- payment, subscription, refund, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Insert base exchange rates (USD as base)
INSERT INTO exchange_rates (rate_id, from_currency, to_currency, rate, provider) VALUES
(uuid_generate_v4(), 'USD', 'EUR', 0.92, 'manual'),
(uuid_generate_v4(), 'USD', 'GBP', 0.79, 'manual'),
(uuid_generate_v4(), 'USD', 'CHF', 0.90, 'manual'),
(uuid_generate_v4(), 'USD', 'ZAR', 18.50, 'manual'),
(uuid_generate_v4(), 'USD', 'CAD', 1.36, 'manual'),
(uuid_generate_v4(), 'USD', 'AUD', 1.52, 'manual'),
(uuid_generate_v4(), 'USD', 'JPY', 155.20, 'manual'),
(uuid_generate_v4(), 'USD', 'CNY', 7.25, 'manual'),
(uuid_generate_v4(), 'USD', 'INR', 83.10, 'manual'),
(uuid_generate_v4(), 'USD', 'BRL', 5.10, 'manual'),
(uuid_generate_v4(), 'USD', 'MXN', 16.80, 'manual')
ON CONFLICT (from_currency, to_currency) DO NOTHING;

-- Insert reverse exchange rates
INSERT INTO exchange_rates (rate_id, from_currency, to_currency, rate, provider) VALUES
(uuid_generate_v4(), 'EUR', 'USD', 1.09, 'manual'),
(uuid_generate_v4(), 'GBP', 'USD', 1.27, 'manual'),
(uuid_generate_v4(), 'CHF', 'USD', 1.11, 'manual'),
(uuid_generate_v4(), 'ZAR', 'USD', 0.054, 'manual'),
(uuid_generate_v4(), 'CAD', 'USD', 0.74, 'manual'),
(uuid_generate_v4(), 'AUD', 'USD', 0.66, 'manual'),
(uuid_generate_v4(), 'JPY', 'USD', 0.0064, 'manual'),
(uuid_generate_v4(), 'CNY', 'USD', 0.138, 'manual'),
(uuid_generate_v4(), 'INR', 'USD', 0.012, 'manual'),
(uuid_generate_v4(), 'BRL', 'USD', 0.196, 'manual'),
(uuid_generate_v4(), 'MXN', 'USD', 0.060, 'manual')
ON CONFLICT (from_currency, to_currency) DO NOTHING;

-- 6. Update existing plans with multi-currency support
-- Add supported currencies to existing plans
UPDATE plans SET supported_currencies = '["USD", "EUR", "GBP", "CHF", "ZAR"]' WHERE name LIKE '%basic%';
UPDATE plans SET supported_currencies = '["USD", "EUR", "GBP", "CHF", "ZAR", "CAD", "AUD"]' WHERE name LIKE '%professional%' OR name LIKE '%pro%';
UPDATE plans SET supported_currencies = '["USD", "EUR", "GBP", "CHF", "ZAR", "CAD", "AUD", "JPY"]' WHERE name LIKE '%enterprise%';

-- Enable geo-pricing for all plans
UPDATE plans SET geo_pricing_enabled = TRUE;

-- 7. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_currency_preferences_user_id ON user_currency_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_currency_preferences_currency ON user_currency_preferences(preferred_currency);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair ON exchange_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_timestamp ON exchange_rates(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_user ON currency_conversion_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_currencies ON currency_conversion_logs(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_invoices_currency ON invoices(currency);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_gateway ON invoices(payment_gateway);
CREATE INDEX IF NOT EXISTS idx_billing_history_currency ON billing_history(currency);

-- 8. Create views for currency reporting
CREATE OR REPLACE VIEW currency_summary AS
SELECT 
    h.currency,
    COUNT(*) as transaction_count,
    SUM(h.amount) as total_amount,
    AVG(h.amount) as average_amount,
    MIN(h.created_at) as first_transaction,
    MAX(h.created_at) as last_transaction
FROM billing_history h 
WHERE h.currency IS NOT NULL
GROUP BY h.currency
ORDER BY total_amount DESC;

CREATE OR REPLACE VIEW gateway_performance AS
SELECT 
    i.payment_gateway,
    i.currency,
    COUNT(*) as transaction_count,
    SUM(i.amount) as total_volume,
    AVG(i.amount) as average_transaction,
    COUNT(CASE WHEN i.status = 'paid' THEN 1 END) as successful_payments,
    COUNT(CASE WHEN i.status = 'failed' THEN 1 END) as failed_payments,
    ROUND(COUNT(CASE WHEN i.status = 'paid' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM invoices i
WHERE i.payment_gateway IS NOT NULL
GROUP BY i.payment_gateway, i.currency
ORDER BY total_volume DESC;

-- 9. Create functions for currency operations
CREATE OR REPLACE FUNCTION get_current_exchange_rate(from_curr VARCHAR(3), to_curr VARCHAR(3))
RETURNS DECIMAL(15,8) AS $$
DECLARE
    rate_value DECIMAL(15,8);
BEGIN
    SELECT rate INTO rate_value 
    FROM exchange_rates 
    WHERE from_currency = from_curr AND to_currency = to_curr 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    IF rate_value IS NULL THEN
        RAISE EXCEPTION 'Exchange rate not found for % to %', from_curr, to_curr;
    END IF;
    
    RETURN rate_value;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION convert_currency(amount DECIMAL(15,2), from_curr VARCHAR(3), to_curr VARCHAR(3))
RETURNS DECIMAL(15,2) AS $$
DECLARE
    rate_value DECIMAL(15,8);
    converted_amount DECIMAL(15,2);
BEGIN
    IF from_curr = to_curr THEN
        RETURN amount;
    END IF;
    
    rate_value := get_current_exchange_rate(from_curr, to_curr);
    converted_amount := amount * rate_value;
    
    RETURN ROUND(converted_amount, 2);
END;
$$ LANGUAGE plpgsql;

-- 10. Add currency validation check constraint
ALTER TABLE plans ADD CONSTRAINT check_supported_currencies 
CHECK (jsonb_typeof(supported_currencies) = 'array' AND jsonb_array_length(supported_currencies) > 0);

ALTER TABLE invoices ADD CONSTRAINT check_currency_format 
CHECK (currency ~ '^[A-Z]{3}$');

ALTER TABLE user_currency_preferences ADD CONSTRAINT check_preferred_currency 
CHECK (preferred_currency ~ '^[A-Z]{3}$');

-- 11. Create trigger to update timestamp on currency preference changes
CREATE OR REPLACE FUNCTION update_currency_preference_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS currency_preference_update_trigger ON user_currency_preferences;
CREATE TRIGGER currency_preference_update_trigger
    BEFORE UPDATE ON user_currency_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_currency_preference_timestamp();

-- 12. Add comments for documentation
COMMENT ON TABLE user_currency_preferences IS 'User currency preferences and localization settings';
COMMENT ON TABLE exchange_rates IS 'Exchange rates between different currencies';
COMMENT ON TABLE currency_conversion_logs IS 'Log of all currency conversions for audit purposes';
COMMENT ON VIEW currency_summary IS 'Summary of transactions by currency';
COMMENT ON VIEW gateway_performance IS 'Performance metrics by payment gateway and currency';

-- 13. Verify migration completion
DO $$
BEGIN
    RAISE NOTICE 'Multi-currency migration completed successfully';
    RAISE NOTICE '- Added multi-currency support to existing tables';
    RAISE NOTICE '- Created user currency preferences table';
    RAISE NOTICE '- Created exchange rates tracking table';
    RAISE NOTICE '- Added currency conversion logging';
    RAISE NOTICE '- Created currency reporting views';
    RAISE NOTICE '- Added currency validation functions';
    RAISE NOTICE '- Inserted base exchange rates (USD as primary currency)';
END $$;