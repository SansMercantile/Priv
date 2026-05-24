"""
PayFast Integration Database Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This migration adds PayFast support to the existing payment system.
Add PayFast as a payment provider and adds necessary fields for PayFast integration.
"""

-- Migration: Add PayFast Payment Provider
-- Date: 2025-06-17
-- Description: Add PayFast payment provider and related fields

-- 1. Update PaymentProvider enum to include PayFast
-- Note: This is handled in the models.py file since SQLAlchemy enums are defined there

-- 2. Add PayFast-specific fields to existing tables
-- Add PayFast plan token to plans table
ALTER TABLE plans 
ADD COLUMN payfast_plan_token VARCHAR(255);

-- Add PayFast subscription token to subscriptions table
ALTER TABLE subscriptions 
ADD COLUMN payfast_subscription_token VARCHAR(255) UNIQUE;

-- Add PayFast invoice token to invoices table
ALTER TABLE invoices 
ADD COLUMN payfast_invoice_token VARCHAR(255) UNIQUE;

-- 3. Create indexes for PayFast fields for performance
CREATE INDEX idx_plans_payfast_token ON plans(payfast_plan_token);
CREATE INDEX idx_subscriptions_payfast_token ON subscriptions(payfast_subscription_token);
CREATE INDEX idx_invoices_payfast_token ON invoices(payfast_invoice_token);

-- 4. Add PayFast configuration table for system-wide settings
CREATE TABLE IF NOT EXISTS payfast_config (
    config_id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(50) NOT NULL,
    merchant_key VARCHAR(100) NOT NULL,
    passphrase VARCHAR(255),
    sandbox BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 5. Insert default PayFast configuration
INSERT INTO payfast_config (config_id, merchant_id, merchant_key, passphrase, sandbox)
VALUES (
    'default-payfast-config',
    '10000100',
    '46f0cd694581a',
    'jt7NOE43FZPn',
    TRUE
) ON CONFLICT (config_id) DO NOTHING;

-- 6. Create PayFast webhook log table for ITN tracking
CREATE TABLE IF NOT EXISTS payfast_webhook_logs (
    log_id VARCHAR(36) PRIMARY KEY,
    itn_data TEXT NOT NULL,
    signature VARCHAR(32),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processed, failed
    error_message TEXT NULL,
    m_payment_id VARCHAR(50),
    subscription_token VARCHAR(255)
);

-- 7. Add indexes for webhook logs
CREATE INDEX idx_payfast_webhook_status ON payfast_webhook_logs(status);
CREATE INDEX idx_payfast_webhook_received ON payfast_webhook_logs(received_at);
CREATE INDEX idx_payfast_webhook_payment ON payfast_webhook_logs(m_payment_id);

-- 8. Update billing history to include PayFast-specific details
-- Add new columns if they don't exist
ALTER TABLE billing_history 
ADD COLUMN IF NOT EXISTS payfast_data JSON;

-- 9. Create system billing plans table for unified management
CREATE TABLE IF NOT EXISTS system_billing_plans (
    plan_id VARCHAR(36) PRIMARY KEY,
    system_name VARCHAR(50) NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'ZAR',
    description TEXT,
    features JSON,
    usage_limits JSON,
    payfast_plan_token VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(system_name, plan_name)
);

-- 10. Add indexes for system billing plans
CREATE INDEX idx_system_billing_system ON system_billing_plans(system_name);
CREATE INDEX idx_system_billing_active ON system_billing_plans(is_active);

-- 11. Insert default plans for each system
INSERT INTO system_billing_plans (plan_id, system_name, plan_name, price, description, features, usage_limits) VALUES
-- Anubis Plans
(uuid_generate_v4(), 'anubis', 'basic', 99.99, 'Basic astroeconomic analysis tools', 
 '["Resource pricing", "Basic route analysis", "Standard reports"]',
 '{"api_calls": 1000, "analysis_reports": 10}'),

(uuid_generate_v4(), 'anubis', 'professional', 299.99, 'Professional astroeconomic suite', 
 '["Advanced resource pricing", "Route optimization", "Custom reports", "API access"]',
 '{"api_calls": 10000, "analysis_reports": 100}'),

(uuid_generate_v4(), 'anubis', 'enterprise', 999.99, 'Enterprise astroeconomic platform', 
 '["Full suite", "Real-time data", "Custom integrations", "Priority support"]',
 '{"api_calls": 100000, "analysis_reports": 1000}'),

-- Brigit Plans
(uuid_generate_v4(), 'brigit', 'starter', 149.99, 'Starter multi-agent system', 
 '["Basic orchestrator", "5 agents", "Standard support"]',
 '{"agents": 5, "tasks_per_month": 100}'),

(uuid_generate_v4(), 'brigit', 'business', 499.99, 'Business multi-agent system', 
 '["Advanced orchestrator", "25 agents", "Priority support", "Custom workflows"]',
 '{"agents": 25, "tasks_per_month": 1000}'),

(uuid_generate_v4(), 'brigit', 'enterprise', 1499.99, 'Enterprise multi-agent platform', 
 '["Full orchestrator", "Unlimited agents", "24/7 support", "Full customization"]',
 '{"agents": "unlimited", "tasks_per_month": "unlimited"}'),

-- Omega Plans
(uuid_generate_v4(), 'omega', 'health_basic', 249.99, 'Basic health management system', 
 '["Patient management", "Basic billing", "Standard reports"]',
 '{"patients": 100, "invoices_per_month": 50}'),

(uuid_generate_v4(), 'omega', 'health_pro', 749.99, 'Professional health platform', 
 '["Full patient management", "Advanced billing", "Analytics", "Integrations"]',
 '{"patients": 1000, "invoices_per_month": 500}'),

-- MPeti Plans
(uuid_generate_v4(), 'mpeti', 'cloud_basic', 179.99, 'Basic cloud operations', 
 '["Multi-cloud support", "Basic monitoring", "Standard support"]',
 '{"cloud_accounts": 3, "apis_per_month": 1000}'),

(uuid_generate_v4(), 'mpeti', 'cloud_enterprise', 679.99, 'Enterprise cloud operations', 
 '["Unlimited clouds", "Advanced monitoring", "24/7 support", "Custom integrations"]',
 '{"cloud_accounts": "unlimited", "apis_per_month": "unlimited"}')

ON CONFLICT DO NOTHING;

-- 12. Create view for active system plans
CREATE OR REPLACE VIEW active_system_plans AS
SELECT 
    plan_id,
    system_name,
    plan_name,
    price,
    currency,
    description,
    features,
    usage_limits,
    payfast_plan_token,
    created_at
FROM system_billing_plans 
WHERE is_active = TRUE;

-- 13. Add comments for documentation
COMMENT ON TABLE payfast_config IS 'PayFast payment gateway configuration';
COMMENT ON TABLE payfast_webhook_logs IS 'Log of PayFast ITN webhook notifications';
COMMENT ON TABLE system_billing_plans IS 'Unified billing plans for all constellation systems';
COMMENT ON VIEW active_system_plans IS 'View of active billing plans for all systems';

-- 14. Create function to update timestamp on config changes
CREATE OR REPLACE FUNCTION update_payfast_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 15. Add trigger for config timestamp updates
DROP TRIGGER IF EXISTS payfast_config_update_trigger ON payfast_config;
CREATE TRIGGER payfast_config_update_trigger
    BEFORE UPDATE ON payfast_config
    FOR EACH ROW
    EXECUTE FUNCTION update_payfast_config_timestamp();

-- 16. Verify migration completion
DO $$
BEGIN
    RAISE NOTICE 'PayFast migration completed successfully';
    RAISE NOTICE '- Added PayFast fields to existing tables';
    RAISE NOTICE '- Created PayFast configuration and logging tables';
    RAISE NOTICE '- Inserted default billing plans for all systems';
    RAISE NOTICE '- Created indexes for performance optimization';
END $$;