import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  Settings,
  Brain,
  Shield,
  Camera,
  Save,
  AlertTriangle,
  TrendingUp,
  Target,
  Zap,
  Lock,
  Unlock,
  X
} from 'lucide-react';
import apiClient from '../../api/apiClient'; 
import './UserProfileEditor.css'; // Make sure to create this CSS file

const UserProfileEditor = ({ demoMode = false }) => {
  // Profile state
  const [profile, setProfile] = useState({
    personal: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      timezone: '',
      language: 'en',
      profilePicture: null
    },
    trading: {
      preferredAssets: [],
      riskTolerance: 'moderate',
      tradingStyle: 'swing',
      emotionalTendencies: [],
      primaryGoals: [],
      tonePreference: 'professional',
      investmentHorizon: 'medium',
      maxPositionSize: 10000,
      stopLossDefault: 2.0,
      takeProfitDefault: 6.0
    },
    aiSettings: {
      enabled: true,
      killSwitchTriggered: false,
      autonomyLevel: 'supervised',
      riskOverride: false,
      maxDailyTrades: 5,
      maxDailyLoss: 1000,
      allowedStrategies: [],
      notificationPreferences: {
        email: true,
        sms: false,
        push: true,
        whatsapp: false
      }
    },
    privacy: {
      dataSharing: false,
      analyticsOptIn: true,
      marketingOptIn: false,
      biometricAuth: false
    }
  });

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');
  const [hasChanges, setHasChanges] = useState(false);
  const [errors, setErrors] = useState({});
  const [showKillSwitchConfirm, setShowKillSwitchConfirm] = useState(false);

  // Available options
  const assetOptions = [
    'Stocks', 'ETFs', 'Options', 'Futures', 'Forex', 'Crypto',
    'Bonds', 'Commodities', 'REITs', 'Indices'
  ];

  const riskToleranceOptions = [
    { value: 'conservative', label: 'Conservative', description: 'Low risk, steady returns' },
    { value: 'moderate', label: 'Moderate', description: 'Balanced risk and return' },
    { value: 'aggressive', label: 'Aggressive', description: 'High risk, high potential returns' },
    { value: 'very_aggressive', label: 'Very Aggressive', description: 'Maximum risk tolerance' }
  ];

  const tradingStyleOptions = [
    { value: 'scalping', label: 'Scalping', description: 'Very short-term trades' },
    { value: 'day', label: 'Day Trading', description: 'Intraday positions' },
    { value: 'swing', label: 'Swing Trading', description: 'Multi-day positions' },
    { value: 'position', label: 'Position Trading', description: 'Long-term positions' }
  ];

  const autonomyLevelOptions = [
    { value: 'manual', label: 'Manual Only', description: 'AI provides recommendations only' },
    { value: 'supervised', label: 'Supervised', description: 'AI executes with approval' },
    { value: 'semi_autonomous', label: 'Semi-Autonomous', description: 'AI executes within limits' },
    { value: 'autonomous', label: 'Autonomous', description: 'Full AI control within parameters' }
  ];

  const strategyOptions = [
    'Trend Following', 'Mean Reversion', 'Momentum', 'Arbitrage',
    'Options Strategies', 'Pairs Trading', 'Breakout', 'Contrarian'
  ];

  // Load profile data
  const loadProfile = useCallback(async () => {
    try {
      setIsLoading(true);
      if (demoMode) {
        return;
      }
      const resp = await apiClient.getUserProfile();
      const profileData = resp?.data || resp || {};
      if (profileData && Object.keys(profileData).length > 0) {
        setProfile((prevProfile) => ({
          ...prevProfile,
          personal: { ...prevProfile.personal, ...profileData.personal },
          trading: { ...prevProfile.trading, ...profileData.trading },
          aiSettings: { ...prevProfile.aiSettings, ...profileData.aiSettings },
        }));
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      setErrors({ general: 'Failed to load profile data' });
    } finally {
      setIsLoading(false);
    }
  }, [demoMode]);

  // Save profile data
  const saveProfile = async () => {
    try {
      setSaving(true);
      setErrors({});

      const validationErrors = validateProfile(profile);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        return;
      }

      if (!demoMode) {
        await apiClient.updateUserProfile(profile);
      }
      setHasChanges(false);
      
      setErrors({ success: 'Profile updated successfully!' });
      setTimeout(() => setErrors(prev => ({...prev, success: null})), 3000);

    } catch (error) {
      console.error('Failed to save profile:', error);
      setErrors({ general: 'Failed to save profile. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  // Validate profile data
  const validateProfile = (profileData) => {
    const errors = {};
    if (!profileData.personal.firstName.trim()) errors.firstName = 'First name is required';
    if (!profileData.personal.lastName.trim()) errors.lastName = 'Last name is required';
    if (!profileData.personal.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(profileData.personal.email)) {
      errors.email = 'Email is invalid';
    }
    if (profileData.trading.maxPositionSize <= 0) errors.maxPositionSize = 'Must be > 0';
    if (profileData.trading.stopLossDefault < 0 || profileData.trading.stopLossDefault > 50) errors.stopLossDefault = 'Must be 0-50%';
    if (profileData.aiSettings.maxDailyTrades <= 0) errors.maxDailyTrades = 'Must be > 0';
    if (profileData.aiSettings.maxDailyLoss <= 0) errors.maxDailyLoss = 'Must be > 0';
    return errors;
  };

  const handleInputChange = (section, field, value) => {
    setProfile(prev => ({ ...prev, [section]: { ...prev[section], [field]: value } }));
    setHasChanges(true);
  };

  const handleNestedInputChange = (section, subsection, field, value) => {
    setProfile(prev => ({ ...prev, [section]: { ...prev[section], [subsection]: { ...prev[section][subsection], [field]: value } } }));
    setHasChanges(true);
  };

  const handleArrayChange = (section, field, value, checked) => {
    setProfile(prev => {
      const currentArray = prev[section][field] || [];
      const newArray = checked ? [...currentArray, value] : currentArray.filter(item => item !== value);
      return { ...prev, [section]: { ...prev[section], [field]: newArray } };
    });
    setHasChanges(true);
  };
  
  const handleKillSwitch = async () => {
    if (!profile.aiSettings.killSwitchTriggered) {
      setShowKillSwitchConfirm(true);
    } else {
      handleInputChange('aiSettings', 'killSwitchTriggered', false);
      await saveProfile();
    }
  };

  const confirmKillSwitch = async () => {
    handleInputChange('aiSettings', 'killSwitchTriggered', true);
    setShowKillSwitchConfirm(false);
    await saveProfile();
  };

  const handleProfilePictureUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      // const uploadResult = await apiClient.uploadFile('/api/v1/profile/picture', file);
      // handleInputChange('personal', 'profilePicture', uploadResult.url);
      const reader = new FileReader();
      reader.onloadend = () => {
        handleInputChange('personal', 'profilePicture', reader.result);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Failed to upload profile picture:', error);
      setErrors({ profilePicture: 'Failed to upload profile picture' });
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    saveProfile();
  };

  const handleCancel = () => {
    loadProfile();
    setHasChanges(false);
    setErrors({});
  };

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  if (isLoading) {
    return <div className="loading-container">Loading profile...</div>;
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'personal':
        return <PersonalTabContent />;
      case 'trading':
        return <TradingTabContent />;
      case 'aiSettings':
        return <AISettingsTabContent />;
      case 'privacy':
        return <PrivacyTabContent />;
      default:
        return null;
    }
  };

  const TabButton = ({ id, label, icon: Icon }) => (
    <button
      className={`tab-button ${activeTab === id ? 'active' : ''}`}
      onClick={() => setActiveTab(id)}
    >
      <Icon size={20} />
      <span>{label}</span>
    </button>
  );

  const InputField = ({ section, field, label, type = 'text', placeholder, error }) => (
    <div className="input-group">
      <label htmlFor={`${section}-${field}`}>{label}</label>
      <input
        id={`${section}-${field}`}
        type={type}
        value={profile[section][field]}
        onChange={(e) => handleInputChange(section, field, e.target.value)}
        placeholder={placeholder}
        className={error ? 'error' : ''}
      />
      {error && <span className="error-message">{error}</span>}
    </div>
  );

  const PersonalTabContent = () => (
    <div className="tab-pane">
        <div className="profile-picture-section">
            <img src={profile.personal.profilePicture || 'https://placehold.co/100x100/e2e8f0/4a5568?text=User'} alt="Profile" className="profile-picture" />
            <label htmlFor="profile-picture-upload" className="upload-button">
                <Camera size={16} /> Change Picture
            </label>
            <input id="profile-picture-upload" type="file" accept="image/*" onChange={handleProfilePictureUpload} style={{ display: 'none' }}/>
        </div>
        <div className="form-grid">
            <InputField section="personal" field="firstName" label="First Name" placeholder="John" error={errors.firstName} />
            <InputField section="personal" field="lastName" label="Last Name" placeholder="Doe" error={errors.lastName} />
            <InputField section="personal" field="email" label="Email" type="email" placeholder="john.doe@example.com" error={errors.email} />
            <InputField section="personal" field="phone" label="Phone Number" type="tel" placeholder="+1 (555) 123-4567" />
            <InputField section="personal" field="timezone" label="Timezone" placeholder="e.g., America/New_York" />
            <InputField section="personal" field="language" label="Language" placeholder="English" />
        </div>
    </div>
  );

  const TradingTabContent = () => (
    <div className="tab-pane">
        <h3 className="section-title">Trading DNA</h3>
        <div className="form-grid">
            <div className="input-group full-width">
                <label>Preferred Assets</label>
                <div className="checkbox-group">
                    {assetOptions.map(opt => (
                        <label key={opt} className="checkbox-label">
                            <input type="checkbox" checked={profile.trading.preferredAssets.includes(opt)} onChange={(e) => handleArrayChange('trading', 'preferredAssets', opt, e.target.checked)} />
                            {opt}
                        </label>
                    ))}
                </div>
            </div>
            <div className="input-group">
                <label>Risk Tolerance</label>
                <select value={profile.trading.riskTolerance} onChange={(e) => handleInputChange('trading', 'riskTolerance', e.target.value)}>
                    {riskToleranceOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            </div>
             <div className="input-group">
                <label>Trading Style</label>
                <select value={profile.trading.tradingStyle} onChange={(e) => handleInputChange('trading', 'tradingStyle', e.target.value)}>
                    {tradingStyleOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            </div>
            <InputField section="trading" field="maxPositionSize" label="Max Position Size ($)" type="number" error={errors.maxPositionSize} />
            <InputField section="trading" field="stopLossDefault" label="Default Stop Loss (%)" type="number" error={errors.stopLossDefault} />
            <InputField section="trading" field="takeProfitDefault" label="Default Take Profit (%)" type="number" />
        </div>
    </div>
  );

  const AISettingsTabContent = () => (
    <div className="tab-pane">
        <div className={`kill-switch-banner ${profile.aiSettings.killSwitchTriggered ? 'active' : ''}`}>
            <AlertTriangle size={24} />
            <p>{profile.aiSettings.killSwitchTriggered ? 'AI Trading is currently EMERGENCY STOPPED.' : 'Emergency AI Kill Switch'}</p>
            <button onClick={handleKillSwitch} className={`kill-switch-button ${profile.aiSettings.killSwitchTriggered ? 'reactivate' : ''}`}>
                {profile.aiSettings.killSwitchTriggered ? <><Unlock size={16}/> Reactivate AI</> : <><Lock size={16}/> Stop AI Trading</>}
            </button>
        </div>
        <h3 className="section-title">AI Configuration</h3>
        <div className="form-grid">
            <div className="input-group toggle-group">
                <label>AI Trading Enabled</label>
                <label className="switch">
                    <input type="checkbox" checked={profile.aiSettings.enabled} onChange={(e) => handleInputChange('aiSettings', 'enabled', e.target.checked)} />
                    <span className="slider round"></span>
                </label>
            </div>
            <div className="input-group">
                <label>Autonomy Level</label>
                <select value={profile.aiSettings.autonomyLevel} onChange={(e) => handleInputChange('aiSettings', 'autonomyLevel', e.target.value)}>
                    {autonomyLevelOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            </div>
            <InputField section="aiSettings" field="maxDailyTrades" label="Max Daily Trades" type="number" error={errors.maxDailyTrades} />
            <InputField section="aiSettings" field="maxDailyLoss" label="Max Daily Loss ($)" type="number" error={errors.maxDailyLoss} />
            <div className="input-group full-width">
                <label>Allowed AI Strategies</label>
                <div className="checkbox-group">
                    {strategyOptions.map(opt => (
                        <label key={opt} className="checkbox-label">
                            <input type="checkbox" checked={profile.aiSettings.allowedStrategies.includes(opt)} onChange={(e) => handleArrayChange('aiSettings', 'allowedStrategies', opt, e.target.checked)} />
                            {opt}
                        </label>
                    ))}
                </div>
            </div>
        </div>
    </div>
  );

  const PrivacyTabContent = () => (
      <div className="tab-pane">
          <h3 className="section-title">Privacy & Data</h3>
          <div className="privacy-grid">
              <div className="input-group toggle-group">
                  <label>Share Anonymized Data</label>
                  <p>Help improve our AI by sharing your anonymized trading data.</p>
                  <label className="switch">
                      <input type="checkbox" checked={profile.privacy.dataSharing} onChange={(e) => handleInputChange('privacy', 'dataSharing', e.target.checked)} />
                      <span className="slider round"></span>
                  </label>
              </div>
              <div className="input-group toggle-group">
                  <label>Enable Usage Analytics</label>
                   <p>Allow us to collect usage data to improve the application.</p>
                  <label className="switch">
                      <input type="checkbox" checked={profile.privacy.analyticsOptIn} onChange={(e) => handleInputChange('privacy', 'analyticsOptIn', e.target.checked)} />
                      <span className="slider round"></span>
                  </label>
              </div>
              <div className="input-group toggle-group">
                  <label>Marketing Communications</label>
                   <p>Receive product updates and marketing emails.</p>
                  <label className="switch">
                      <input type="checkbox" checked={profile.privacy.marketingOptIn} onChange={(e) => handleInputChange('privacy', 'marketingOptIn', e.target.checked)} />
                      <span className="slider round"></span>
                  </label>
              </div>
          </div>
      </div>
  );

  return (
    <div className="user-profile-editor">
      <header className="profile-header">
        <h1>User Profile & Settings</h1>
        <p>Manage your personal information, trading preferences, and AI settings.</p>
      </header>

      <form onSubmit={handleSubmit} className="profile-form">
        <nav className="profile-tabs">
          <TabButton id="personal" label="Personal" icon={User} />
          <TabButton id="trading" label="Trading" icon={TrendingUp} />
          <TabButton id="aiSettings" label="AI Settings" icon={Brain} />
          <TabButton id="privacy" label="Privacy" icon={Shield} />
        </nav>

        <div className="tab-content">
            {renderTabContent()}
        </div>
        
        <footer className="profile-footer">
            {errors.general && <div className="error-banner">{errors.general}</div>}
            {errors.success && <div className="success-banner">{errors.success}</div>}
            <div className="footer-buttons">
                <button type="button" className="button-secondary" onClick={handleCancel} disabled={!hasChanges || isSaving}>
                    Cancel
                </button>
                <button type="submit" className="button-primary" disabled={!hasChanges || isSaving}>
                    <Save size={16} /> {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
            </div>
        </footer>
      </form>

      {showKillSwitchConfirm && (
        <div className="modal-backdrop">
            <div className="modal-content">
                <button className="modal-close" onClick={() => setShowKillSwitchConfirm(false)}><X size={20}/></button>
                <AlertTriangle size={48} className="modal-icon" />
                <h2>Confirm AI Shutdown</h2>
                <p>
                    Are you sure you want to trigger the emergency kill switch? This will immediately halt all AI-managed trading activity and liquidate open positions managed by the AI according to safety protocols.
                </p>
                <div className="modal-actions">
                    <button onClick={() => setShowKillSwitchConfirm(false)} className="button-secondary">Cancel</button>
                    <button onClick={confirmKillSwitch} className="button-danger">Confirm Shutdown</button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}

export default UserProfileEditor;
