// src/pages/CreateProfilePage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth'; 
import apiClient from '../api/apiClient'; 
import { LogoIcon } from '../components/icons/Icons';
import { useEnvironment } from '../context/EnvironmentContext';

export default function CreateProfilePage() {
    const [profile, setProfile] = useState({ fullName: '', idNumber: '', address: '' });
    const [error, setError] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [policyRead, setPolicyRead] = useState({
        eula: false,
        privacy: false,
        compliance: false,
        liability: false,
        terms: false,
    });
    const [policyAccepted, setPolicyAccepted] = useState({
        eula: false,
        privacy: false,
        compliance: false,
        liability: false,
        terms: false,
    });
    const [agentsList, setAgentsList] = useState([]);
    const [countriesList, setCountriesList] = useState([]);
    const [selectedAgents, setSelectedAgents] = useState([]);
    const [selectedTaxResidency, setSelectedTaxResidency] = useState(null);
    const navigate = useNavigate();
    const { markOnboardingComplete } = useAuth();
    const { setDemoMode } = useEnvironment();

    // Load demo data for agents and supported tax countries
    useEffect(() => {
        let mounted = true;
        (async () => {
            try {
                const agentsResp = await apiClient.getAgentStatus();
                if (mounted && agentsResp && agentsResp.agents) setAgentsList(agentsResp.agents);
                const countries = await apiClient.getSupportedTaxCountries();
                if (mounted && Array.isArray(countries)) setCountriesList(countries);

                // Load existing profile choices
                const existingProfileResp = await apiClient.getUserProfile();
                const existing = existingProfileResp?.data || {};
                if (existing?.preferred_agents) setSelectedAgents(existing.preferred_agents || []);
                if (existing?.tax_residency) setSelectedTaxResidency(existing.tax_residency);
            } catch (err) {
                console.warn('Failed to load agents/countries:', err);
            }
        })();
        return () => { mounted = false; };
    }, []);


    const handleChange = (e) => {
        setProfile(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handlePolicyRead = (policy) => {
        setPolicyRead(prev => ({ ...prev, [policy]: true }));
    };

    const handlePolicyAccept = (policy) => {
        setPolicyAccepted(prev => ({ ...prev, [policy]: !prev[policy] }));
    };

    const allPoliciesRead = Object.values(policyRead).every(Boolean);
    const allPoliciesAccepted = Object.values(policyAccepted).every(Boolean);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!allPoliciesRead || !allPoliciesAccepted) {
            setError('You must read and accept all policies to continue.');
            return;
        }
        setIsSaving(true);
        try {
            // Fetch current profile (demo or persisted)
            const existingProfileResp = await apiClient.getUserProfile();
            const existingProfile = existingProfileResp?.data || {};

            const updatedProfile = {
                ...existingProfile,
                full_legal_name: profile.fullName,
                id_passport_number: profile.idNumber,
                residential_address: profile.address,
                agreed_policies: Object.keys(policyAccepted).filter(k => policyAccepted[k]),
                preferred_agents: selectedAgents,
                tax_residency: selectedTaxResidency,
            };

            await apiClient.updateUserProfile(updatedProfile);
            markOnboardingComplete();
            navigate('/verification');
        } catch (err) {
            setError(err.message || 'Failed to save profile.');
        } finally {
            setIsSaving(false);
        }
    };

    // If user declines any policy, return to demo mode
    const handleDecline = () => {
        setError('You must accept all policies to use live mode. Returning to demo mode.');
        setDemoMode(true);
        navigate('/dashboard');
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-main-bg p-4 font-body">
            <div className="bg-card-bg p-8 rounded-lg shadow-xl w-full max-w-md text-center">
                <div className="flex justify-center mb-6"><LogoIcon className="h-24 w-24 object-contain" /></div>
                <h2 className="text-2xl font-bold text-text-primary mb-1">Create Your Profile</h2>
                <p className="text-text-secondary mb-6">Let's get your account set up.</p>
                <form onSubmit={handleSubmit} className="space-y-4 text-left">
                    {error && <p className="text-center text-red-500 text-sm">{error}</p>}
                    <div>
                        <label htmlFor="fullName" className="block text-sm font-medium text-text-primary mb-1">Full Legal Name</label>
                        <input id="fullName" name="fullName" type="text" value={profile.fullName} onChange={handleChange} required className="w-full p-3 rounded-lg bg-input-bg text-text-primary" />
                    </div>
                    <div>
                        <label htmlFor="idNumber" className="block text-sm font-medium text-text-primary mb-1">ID / Passport Number</label>
                        <input id="idNumber" name="idNumber" type="text" value={profile.idNumber} onChange={handleChange} required className="w-full p-3 rounded-lg bg-input-bg text-text-primary" />
                    </div>
                    <div>
                        <label htmlFor="address" className="block text-sm font-medium text-text-primary mb-1">Residential Address</label>
                        <textarea id="address" name="address" value={profile.address} onChange={handleChange} required rows="3" className="w-full p-3 rounded-lg bg-input-bg text-text-primary resize-none" />
                    </div>
                    <div className="mt-6 mb-2">
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Please read and accept all policies:</h3>
                        <ul className="space-y-2">
                            <li>
                                <a href="https://www.sansmercantile.com/eula.html" target="_blank" rel="noopener noreferrer" onClick={() => handlePolicyRead('eula')} className="text-blue-600 underline">End User License Agreement (EULA)</a>
                                <label className="ml-2">
                                    <input type="checkbox" checked={policyAccepted.eula} disabled={!policyRead.eula} onChange={() => handlePolicyAccept('eula')} /> Accept
                                </label>
                            </li>
                            <li>
                                <a href="https://www.sansmercantile.com/policy.html" target="_blank" rel="noopener noreferrer" onClick={() => handlePolicyRead('privacy')} className="text-blue-600 underline">Privacy Policy</a>
                                <label className="ml-2">
                                    <input type="checkbox" checked={policyAccepted.privacy} disabled={!policyRead.privacy} onChange={() => handlePolicyAccept('privacy')} /> Accept
                                </label>
                            </li>
                            <li>
                                <a href="https://www.sansmercantile.com/compliance.html" target="_blank" rel="noopener noreferrer" onClick={() => handlePolicyRead('compliance')} className="text-blue-600 underline">Compliance Statement</a>
                                <label className="ml-2">
                                    <input type="checkbox" checked={policyAccepted.compliance} disabled={!policyRead.compliance} onChange={() => handlePolicyAccept('compliance')} /> Accept
                                </label>
                            </li>
                            <li>
                                <a href="https://www.sansmercantile.com/liability.html" target="_blank" rel="noopener noreferrer" onClick={() => handlePolicyRead('liability')} className="text-blue-600 underline">Liability Disclaimer</a>
                                <label className="ml-2">
                                    <input type="checkbox" checked={policyAccepted.liability} disabled={!policyRead.liability} onChange={() => handlePolicyAccept('liability')} /> Accept
                                </label>
                            </li>
                            <li>
                                <a href="https://www.sansmercantile.com/terms.html" target="_blank" rel="noopener noreferrer" onClick={() => handlePolicyRead('terms')} className="text-blue-600 underline">Terms & Conditions</a>
                                <label className="ml-2">
                                    <input type="checkbox" checked={policyAccepted.terms} disabled={!policyRead.terms} onChange={() => handlePolicyAccept('terms')} /> Accept
                                </label>
                            </li>
                        </ul>
                        <button type="button" className="mt-4 text-red-600 underline" onClick={handleDecline}>Decline & Return to Demo Mode</button>
                    </div>

                    {/* Agent preferences */}
                    <div className="mt-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Preferred Agents</h3>
                        <p className="text-sm text-text-secondary mb-2">Select agents you'd like enabled by default for your account.</p>
                        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-auto p-2 bg-input-bg rounded">
                            {agentsList && agentsList.length > 0 ? (
                                agentsList.map(agent => (
                                    <label key={agent.id} className="flex items-center space-x-2 p-2 rounded hover:bg-card-hover">
                                        <input type="checkbox" checked={selectedAgents.includes(agent.id)} onChange={() => {
                                            setSelectedAgents(prev => prev.includes(agent.id) ? prev.filter(a=>a!==agent.id) : [...prev, agent.id]);
                                        }} />
                                        <span className="text-sm">{agent.name}</span>
                                    </label>
                                ))
                            ) : (
                                <div className="text-sm text-text-secondary">No agents available</div>
                            )}
                        </div>
                    </div>

                    {/* Tax residency */}
                    <div className="mt-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Tax Residency & Reporting</h3>
                        <p className="text-sm text-text-secondary mb-2">Select your primary tax residency to enable country-specific reporting.</p>
                        <select value={selectedTaxResidency || ''} onChange={(e) => setSelectedTaxResidency(e.target.value)} className="w-full p-3 rounded-lg bg-input-bg text-text-primary">
                            <option value="">Select country</option>
                            {countriesList && countriesList.map(c => (
                                <option key={c.code} value={c.code}>{c.name} ({c.code}) - {c.tax_authority || ''}</option>
                            ))}
                        </select>
                    </div>

                    <div className="mt-6 p-4 bg-yellow-100 rounded-lg text-yellow-800 text-sm">
                        <strong>Trading Risk Disclaimer:</strong> Trading financial instruments involves significant risk. Past performance does not guarantee future results. The AI system may make mistakes, even though it has self-healing functions and tests all strategies in a sandbox before live deployment. <strong>Sans Mercantile does not assume responsibility for any losses incurred.</strong>
                    </div>
                    <button type="submit" disabled={isSaving || !allPoliciesRead || !allPoliciesAccepted} className="w-full bg-accent-primary text-white font-semibold py-3 rounded-lg disabled:opacity-50">
                        {isSaving ? 'Saving...' : 'Complete Profile & Continue'}
                    </button>
                </form>
            </div>
        </div>
    );
}
