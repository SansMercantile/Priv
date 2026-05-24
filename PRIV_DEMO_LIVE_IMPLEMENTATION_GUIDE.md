# PRIV Demo-to-Live Transition Implementation Guide

## Overview

This guide details the improvements made to separate demo and live environments in the PRIV application. All mock data is now centralized and only used in demo mode, while live mode requires KYC, profile completion, and broker connections.

## Architecture Changes

### 1. Enhanced Environment Context
**Location**: `/src/context/EnvironmentContext.tsx`

**Features**:
- Tracks `demoMode` boolean state
- Provides `environmentType` ('demo' | 'live')
- Exposes `getEnvironmentRequirements()` method
- Includes better toast notifications with guidance

**Usage**:
```typescript
import { useEnvironment } from '../context/EnvironmentContext';

function MyComponent() {
  const { demoMode, environmentType, getEnvironmentRequirements } = useEnvironment();
  
  const requirements = getEnvironmentRequirements();
  if (!demoMode && requirements.requiresKYC) {
    // Show KYC prompt
  }
}
```

### 2. Centralized Demo Data
**Location**: `/src/data/demoMocks.ts`

**Exported Constants**:
- `DEMO_POSITIONS` - Sample portfolio positions
- `DEMO_TRADING_HISTORY` - Sample past trades
- `DEMO_ALERTS` - Sample notifications
- `DEMO_HISTORY_RECORDS` - Sample transaction history
- `DEMO_CONNECTION_NODES` - Sample network nodes
- `DEMO_NEWS_ARTICLES` - Sample market news
- `DEMO_USER_PROFILE` - Demo user profile
- `DEMO_KYC_STATUS` - Demo KYC verification state
- `DEMO_BROKER_CONNECTIONS` - Demo broker accounts
- `DEMO_RISK_ANALYSIS` - Sample risk metrics

**Important**: Import and use these ONLY in demo mode branches.

### 3. Intelligent Data Fetcher
**Location**: `/src/lib/dataFetcher.ts`

**Purpose**: Routes data requests to mock data (demo) or real APIs (live)

**Available Functions**:
- `fetchPortfolioPositions(options)`
- `fetchTradingHistory(options)`
- `fetchRiskAnalysis(options)`
- `fetchAlerts(options)`
- `fetchUserProfile(options)`
- `fetchKycStatus(options)`
- `fetchBrokerConnections(options)`
- `fetchConnectionNodes(options)`
- `fetchExecutionHistory(options)`
- `fetchNews(options)`
- `fetchDashboardStats(options)`

**Usage**:
```typescript
import { fetchPortfolioPositions } from '../lib/dataFetcher';
import { useEnvironment } from '../context/EnvironmentContext';

function PortfolioView() {
  const { demoMode } = useEnvironment();
  
  const loadPositions = async () => {
    const result = await fetchPortfolioPositions({
      demoMode,
      apiBaseUrl: process.env.REACT_APP_API_BASE_URL,
      userId: currentUser?.id,
    });
    
    if (result.success) {
      setPositions(result.data);
    }
  };
}
```

### 4. Enhanced Demo Environment Notification
**Location**: `/src/components/DemoEnvironmentNotification.tsx`

**Purpose**: Shows users what's available in demo vs live mode

**Props**:
- `visible: boolean` - Whether modal is shown
- `onClose: () => void` - Handler for closing modal
- `demoMode: boolean` - Current environment

**Usage**:
```typescript
import DemoEnvironmentNotification from '../components/DemoEnvironmentNotification';
import { useEnvironment } from '../context/EnvironmentContext';

function App() {
  const { demoMode, lastToggleTime } = useEnvironment();
  const [showDemoModal, setShowDemoModal] = useState(false);
  
  // Show modal when mode is toggled
  useEffect(() => {
    setShowDemoModal(true);
  }, [lastToggleTime]);
  
  return (
    <>
      <DemoEnvironmentNotification
        visible={showDemoModal}
        onClose={() => setShowDemoModal(false)}
        demoMode={demoMode}
      />
    </>
  );
}
```

## Environment Requirements

### Demo Mode
- ✅ No KYC required
- ✅ No profile completion needed
- ✅ No broker connection needed
- ✅ Mock data available
- ❌ No real-time data
- ❌ No real trading

### Live Mode
- ⚠️ **Requires**: Complete KYC verification
  - Government-issued ID verification
  - Address verification
  - Identity document verification
  
- ⚠️ **Requires**: Profile customization
  - Full legal name
  - Trading knowledge level
  - Risk appetite assessment
  - Trading goals
  - Profile picture
  - Tax residency information

- ⚠️ **Requires**: Broker connection
  - Link real or paper trading account
  - OAuth authorization with broker
  - Account synchronization

- ✅ Real-time market data
- ✅ Real account trading
- ✅ Live AI analysis

## KYC Flow Integration

The backend `/api/v1/kyc` endpoint provides:
- Personal information collection
- Identity document upload & verification
- Residential address verification
- Financial profile assessment
- Trading profile questionnaire
- Tax compliance declarations
- Contact verification

**Backend KYC Models** (from `kyc_api.py`):
- `PersonalInfo`
- `IdentityDocument`
- `ResidentialAddress`
- `FinancialProfile`
- `TradingProfileKyc`
- `TaxCompliance`
- `ContactVerification`
- `KycDeclarations`

## Broker Connection Flow

**Backend Endpoints** (from `broker_endpoints.py`):
- `POST /api/v1/brokers/connect` - Initiate broker connection
- `GET /api/v1/brokers/connections` - List connected brokers
- `POST /api/v1/brokers/{broker}/callback` - OAuth callback handler
- `GET /api/v1/brokers/{broker}/accounts` - List broker accounts

**Supported Brokers**:
- Interactive Brokers (IB)
- Alpaca
- Binance
- Deriv
- MetaTrader 5 (MT5)

## Component Integration Checklist

When building components that show different content based on environment:

```typescript
// ✅ DO: Check environment at fetch time
const { demoMode } = useEnvironment();
const data = await fetchData({ demoMode, ...options });

// ✅ DO: Use data fetcher for all data needs
import { fetchPortfolioPositions } from '../lib/dataFetcher';

// ❌ DON'T: Hardcode demo data in components
// Bad:
const POSITIONS = [{ instrument: 'SPX', ... }]; // Wrong!

// ✅ DO: Import from demoMocks only in demo branches
if (demoMode) {
  setPositions(DEMO_POSITIONS); // Correct!
}
```

## Page Status & Integration

The following pages are now properly integrated:

### Fully Connected Pages
- Dashboard
- Trading Terminal
- Portfolio Management
- Risk Analysis
- Connections
- Broker Integration
- Alerts
- News & Analytics

### Partially Connected Pages
- KYC Verification (backend integrated, UI enhancements available)
- Profile (needs refactoring for unified experience)
- Onboarding (spans multiple steps)

### Pages Ready for Enhancement
- Audio Page
- Vision Page
- Wallet & Funding
- Ventures
- Legal

## Testing Guide

### Test Demo Mode
1. Navigate to login page
2. Click "Explore demo environment"
3. Verify mock data is shown
4. Check demo banner at top
5. Try switching to live mode - should show requirements

### Test Live Mode Requirements
1. Switch to live mode
2. Attempt to access portfolio - should prompt for KYC
3. Complete KYC flow
4. Profile page should allow customization
5. Broker connection required for real data

### Test Data Fetcher
```typescript
// In component
const { demoMode } = useEnvironment();
const positions = await fetchPortfolioPositions({ demoMode });
// Should return DEMO_POSITIONS if demo, API data if live
```

## API Configuration

### Backend Setup
Ensure these environment variables are set:

```bash
DEMO_MODE=false  # Set to true for demo mode
GCP_PROJECT_ID=your-project-id
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend Setup
```bash
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENV=production  # or development
```

## Migration Path for Existing Components

If you have existing components using hardcoded demo data:

### Before
```typescript
export function MyComponent() {
  const [data] = useState({
    positions: [{ symbol: 'SPX', price: 4150 }],
  });
  return <div>{data.positions[0].symbol}</div>;
}
```

### After
```typescript
import { useEnvironment } from '../context/EnvironmentContext';
import { fetchPortfolioPositions } from '../lib/dataFetcher';

export function MyComponent() {
  const { demoMode } = useEnvironment();
  const [positions, setPositions] = useState([]);
  
  useEffect(() => {
    const load = async () => {
      const result = await fetchPortfolioPositions({ demoMode });
      if (result.success) setPositions(result.data);
    };
    load();
  }, [demoMode]);
  
  return <div>{positions[0]?.symbol}</div>;
}
```

## Troubleshooting

**Q: Mock data is showing in live mode**
A: Check that all data fetches use the `dataFetcher.ts` utilities and respect the `demoMode` flag.

**Q: KYC modal doesn't appear**
A: Ensure `KycVerificationPage` is rendered in the routing and environment check is implemented.

**Q: Broker connection fails**
A: Verify broker API credentials in backend, check OAuth redirect URLs are configured correctly.

**Q: Toast notifications not showing**
A: Ensure `Toaster` component is mounted in your root app component.

## Future Enhancements

1. **Persistent KYC State**: Store KYC progress in backend
2. **Profile Syncing**: Keep profile data synced across sessions
3. **Broker Data Caching**: Cache broker data to reduce API calls
4. **Advanced Analytics**: Real-time portfolio tracking in live mode
5. **Audit Logging**: Track all user actions and KYC events
6. **Multi-Language Support**: Localize KYC and profile forms

## Support & Questions

For questions about the implementation:
1. Check this guide first
2. Review the component implementations
3. Check backend API documentation
4. File an issue with reproduction steps
