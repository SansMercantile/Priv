import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/apiClient';
import { useAuth } from '../auth/useAuth';
import { setKycStatus as persistKycStatus } from '../lib/environment';

const STEPS = [
  'Legal & Identity',
  'Address',
  'Financial & Trading',
  'Tax & Compliance',
  'Documents',
  'Contact & Review',
];

const INCOME_RANGES = ['< R50k', 'R50k–R200k', 'R200k–R500k', 'R500k–R1m', '> R1m'];
const EXPERIENCE = ['None', '< 1 year', '1–3 years', '3–5 years', '5+ years'];
const RISK_LEVELS = ['Conservative', 'Moderate', 'Aggressive', 'Very aggressive'];
const DOC_TYPES = [
  { value: 'passport', label: 'Passport' },
  { value: 'national_id', label: 'National ID card' },
  { value: 'drivers_license', label: "Driver's licence" },
  { value: 'residence_permit', label: 'Residence permit' },
];

const emptyForm = () => ({
  personal: {
    legal_first_name: '',
    legal_middle_name: '',
    legal_last_name: '',
    date_of_birth: '',
    gender: '',
    nationality: '',
    country_of_residence: '',
    place_of_birth: '',
  },
  identity: {
    document_type: 'passport',
    document_number: '',
    issuing_country: '',
    issue_date: '',
    expiry_date: '',
  },
  address: {
    street_line_1: '',
    street_line_2: '',
    city: '',
    province_state: '',
    postal_code: '',
    country: '',
  },
  financial: {
    employment_status: '',
    employer_name: '',
    occupation: '',
    source_of_funds: '',
    annual_income_range: '',
    net_worth_range: '',
    is_politically_exposed: false,
    pep_details: '',
  },
  trading: {
    years_trading_experience: '',
    trading_knowledge_level: '',
    products_traded: [],
    risk_appetite: '',
    investment_objectives: [],
  },
  tax: {
    tax_residency_country: '',
    tax_identification_number: '',
    us_person_fatca: false,
    fatca_declaration_acknowledged: false,
  },
  contact: {
    email: '',
    email_verified: false,
    phone_country_code: '+27',
    phone_number: '',
    phone_verified: false,
  },
  declarations: {
    terms_accepted: false,
    privacy_accepted: false,
    aml_consent: false,
    sanctions_screening_consent: false,
    accurate_information_declaration: false,
  },
});

function Field({ label, children, required }) {
  return (
    <label className="block text-sm">
      <span className="text-text-primary font-medium">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

function inputClass() {
  return 'w-full p-3 rounded-lg bg-input-bg text-text-primary border border-border-color focus:ring-2 focus:ring-accent-primary';
}

export default function KycVerificationPage({ demoMode = false }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [uploads, setUploads] = useState({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completion, setCompletion] = useState(0);

  useEffect(() => {
    if (user?.email) {
      setForm((f) => ({
        ...f,
        contact: { ...f.contact, email: user.email, email_verified: !!user.emailVerified },
      }));
    }
  }, [user]);

  useEffect(() => {
    if (demoMode) return;
    (async () => {
      try {
        const resp = await apiClient.getKycRecord();
        const data = resp?.data || resp;
        if (data?.personal) {
          setForm((f) => ({
            personal: { ...f.personal, ...data.personal },
            identity: { ...f.identity, ...data.identity },
            address: { ...f.address, ...data.address },
            financial: { ...f.financial, ...data.financial },
            trading: { ...f.trading, ...data.trading },
            tax: { ...f.tax, ...data.tax },
            contact: { ...f.contact, ...data.contact },
            declarations: { ...f.declarations, ...data.declarations },
          }));
        }
        const st = await apiClient.getKycStatus();
        setCompletion(st?.data?.completion_percent ?? 0);
      } catch (e) {
        console.warn('KYC load', e);
      }
    })();
  }, [demoMode]);

  const patch = (section, field, value) => {
    setForm((f) => ({ ...f, [section]: { ...f[section], [field]: value } }));
  };

  const saveDraft = useCallback(async () => {
    if (demoMode) return;
    setSaving(true);
    try {
      await apiClient.saveKycDraft(form);
      const st = await apiClient.getKycStatus();
      setCompletion(st?.data?.completion_percent ?? 0);
    } catch (e) {
      console.warn('Draft save failed', e);
    } finally {
      setSaving(false);
    }
  }, [demoMode, form]);

  const handleUpload = async (file, docType) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      if (demoMode) {
        setUploads((u) => ({ ...u, [docType]: { filename: file.name, document_type: docType } }));
      } else {
        const res = await apiClient.submitKYCDocument(file, docType);
        setUploads((u) => ({ ...u, [docType]: res?.data || res }));
      }
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const next = async () => {
    setError(null);
    await saveDraft();
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const back = () => setStep((s) => Math.max(s - 1, 0));

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    if (demoMode) {
      persistKycStatus('submitted');
      navigate('/dashboard');
      return;
    }
    try {
      await apiClient.submitKyc(form);
      persistKycStatus('submitted');
      navigate('/dashboard');
    } catch (e) {
      const detail = e.response?.data?.detail;
      if (detail?.validation_errors) {
        setError(detail.validation_errors.join('; '));
      } else {
        setError(typeof detail === 'string' ? detail : e.message || 'Submission failed');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Legal first name" required>
              <input className={inputClass()} value={form.personal.legal_first_name} onChange={(e) => patch('personal', 'legal_first_name', e.target.value)} />
            </Field>
            <Field label="Legal middle name">
              <input className={inputClass()} value={form.personal.legal_middle_name} onChange={(e) => patch('personal', 'legal_middle_name', e.target.value)} />
            </Field>
            <Field label="Legal last name" required>
              <input className={inputClass()} value={form.personal.legal_last_name} onChange={(e) => patch('personal', 'legal_last_name', e.target.value)} />
            </Field>
            <Field label="Date of birth" required>
              <input type="date" className={inputClass()} value={form.personal.date_of_birth} onChange={(e) => patch('personal', 'date_of_birth', e.target.value)} />
            </Field>
            <Field label="Gender">
              <select className={inputClass()} value={form.personal.gender} onChange={(e) => patch('personal', 'gender', e.target.value)}>
                <option value="">Prefer not to say</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </Field>
            <Field label="Nationality" required>
              <input className={inputClass()} value={form.personal.nationality} onChange={(e) => patch('personal', 'nationality', e.target.value)} placeholder="e.g. South African" />
            </Field>
            <Field label="Country of residence" required>
              <input className={inputClass()} value={form.personal.country_of_residence} onChange={(e) => patch('personal', 'country_of_residence', e.target.value)} />
            </Field>
            <Field label="Place of birth">
              <input className={inputClass()} value={form.personal.place_of_birth} onChange={(e) => patch('personal', 'place_of_birth', e.target.value)} />
            </Field>
            <Field label="ID document type" required>
              <select className={inputClass()} value={form.identity.document_type} onChange={(e) => patch('identity', 'document_type', e.target.value)}>
                {DOC_TYPES.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Document number" required>
              <input className={inputClass()} value={form.identity.document_number} onChange={(e) => patch('identity', 'document_number', e.target.value)} />
            </Field>
            <Field label="Issuing country" required>
              <input className={inputClass()} value={form.identity.issuing_country} onChange={(e) => patch('identity', 'issuing_country', e.target.value)} />
            </Field>
            <Field label="Issue date">
              <input type="date" className={inputClass()} value={form.identity.issue_date} onChange={(e) => patch('identity', 'issue_date', e.target.value)} />
            </Field>
            <Field label="Expiry date">
              <input type="date" className={inputClass()} value={form.identity.expiry_date} onChange={(e) => patch('identity', 'expiry_date', e.target.value)} />
            </Field>
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Street address" required>
              <input className={inputClass()} value={form.address.street_line_1} onChange={(e) => patch('address', 'street_line_1', e.target.value)} />
            </Field>
            <Field label="Street line 2">
              <input className={inputClass()} value={form.address.street_line_2} onChange={(e) => patch('address', 'street_line_2', e.target.value)} />
            </Field>
            <Field label="City" required>
              <input className={inputClass()} value={form.address.city} onChange={(e) => patch('address', 'city', e.target.value)} />
            </Field>
            <Field label="Province / State">
              <input className={inputClass()} value={form.address.province_state} onChange={(e) => patch('address', 'province_state', e.target.value)} />
            </Field>
            <Field label="Postal code">
              <input className={inputClass()} value={form.address.postal_code} onChange={(e) => patch('address', 'postal_code', e.target.value)} />
            </Field>
            <Field label="Country" required>
              <input className={inputClass()} value={form.address.country} onChange={(e) => patch('address', 'country', e.target.value)} />
            </Field>
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Employment status" required>
              <select className={inputClass()} value={form.financial.employment_status} onChange={(e) => patch('financial', 'employment_status', e.target.value)}>
                <option value="">Select</option>
                <option value="employed">Employed</option>
                <option value="self_employed">Self-employed</option>
                <option value="unemployed">Unemployed</option>
                <option value="retired">Retired</option>
                <option value="student">Student</option>
              </select>
            </Field>
            <Field label="Employer name">
              <input className={inputClass()} value={form.financial.employer_name} onChange={(e) => patch('financial', 'employer_name', e.target.value)} />
            </Field>
            <Field label="Occupation">
              <input className={inputClass()} value={form.financial.occupation} onChange={(e) => patch('financial', 'occupation', e.target.value)} />
            </Field>
            <Field label="Source of funds" required>
              <select className={inputClass()} value={form.financial.source_of_funds} onChange={(e) => patch('financial', 'source_of_funds', e.target.value)}>
                <option value="">Select</option>
                <option value="salary">Salary</option>
                <option value="business">Business income</option>
                <option value="investments">Investments</option>
                <option value="inheritance">Inheritance</option>
                <option value="savings">Savings</option>
              </select>
            </Field>
            <Field label="Annual income range">
              <select className={inputClass()} value={form.financial.annual_income_range} onChange={(e) => patch('financial', 'annual_income_range', e.target.value)}>
                <option value="">Select</option>
                {INCOME_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Net worth range">
              <select className={inputClass()} value={form.financial.net_worth_range} onChange={(e) => patch('financial', 'net_worth_range', e.target.value)}>
                <option value="">Select</option>
                {INCOME_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Years trading experience" required>
              <select className={inputClass()} value={form.trading.years_trading_experience} onChange={(e) => patch('trading', 'years_trading_experience', e.target.value)}>
                <option value="">Select</option>
                {EXPERIENCE.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Trading knowledge" required>
              <select className={inputClass()} value={form.trading.trading_knowledge_level} onChange={(e) => patch('trading', 'trading_knowledge_level', e.target.value)}>
                <option value="">Select</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="professional">Professional</option>
              </select>
            </Field>
            <Field label="Risk appetite" required>
              <select className={inputClass()} value={form.trading.risk_appetite} onChange={(e) => patch('trading', 'risk_appetite', e.target.value)}>
                <option value="">Select</option>
                {RISK_LEVELS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <div className="md:col-span-2 flex items-center gap-2">
              <input type="checkbox" checked={form.financial.is_politically_exposed} onChange={(e) => patch('financial', 'is_politically_exposed', e.target.checked)} />
              <span className="text-sm text-text-secondary">I am a politically exposed person (PEP)</span>
            </div>
            {form.financial.is_politically_exposed && (
              <Field label="PEP details" required>
                <textarea className={inputClass()} rows={2} value={form.financial.pep_details} onChange={(e) => patch('financial', 'pep_details', e.target.value)} />
              </Field>
            )}
          </div>
        );
      case 3:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Tax residency country" required>
              <input className={inputClass()} value={form.tax.tax_residency_country} onChange={(e) => patch('tax', 'tax_residency_country', e.target.value)} />
            </Field>
            <Field label="Tax ID / TRN">
              <input className={inputClass()} value={form.tax.tax_identification_number} onChange={(e) => patch('tax', 'tax_identification_number', e.target.value)} />
            </Field>
            <div className="md:col-span-2 space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.tax.us_person_fatca} onChange={(e) => patch('tax', 'us_person_fatca', e.target.checked)} />
                I am a US person for FATCA purposes
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.tax.fatca_declaration_acknowledged} onChange={(e) => patch('tax', 'fatca_declaration_acknowledged', e.target.checked)} />
                I acknowledge FATCA/CRS reporting obligations
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.declarations.terms_accepted} onChange={(e) => patch('declarations', 'terms_accepted', e.target.checked)} />
                I accept Terms & Conditions
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.declarations.privacy_accepted} onChange={(e) => patch('declarations', 'privacy_accepted', e.target.checked)} />
                I accept the Privacy Policy
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.declarations.aml_consent} onChange={(e) => patch('declarations', 'aml_consent', e.target.checked)} />
                I consent to AML/KYC screening
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.declarations.sanctions_screening_consent} onChange={(e) => patch('declarations', 'sanctions_screening_consent', e.target.checked)} />
                I consent to sanctions list screening
              </label>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">Upload clear colour copies (JPEG, PNG, or PDF, max 10MB each).</p>
            {[
              { key: 'id_front', label: 'ID / Passport — front' },
              { key: 'id_back', label: 'ID — back (if applicable)' },
              { key: 'proof_of_address', label: 'Proof of address (utility bill, bank statement < 3 months)' },
              { key: 'selfie', label: 'Selfie / liveness photo' },
            ].map(({ key, label }) => (
              <div key={key} className="border border-border-color rounded-lg p-4">
                <p className="font-medium text-text-primary text-sm mb-2">{label}</p>
                <input type="file" accept="image/jpeg,image/png,application/pdf" onChange={(e) => handleUpload(e.target.files[0], key)} />
                {uploads[key] && <p className="text-xs text-green-600 mt-1">Uploaded: {uploads[key].filename || key}</p>}
              </div>
            ))}
            {uploading && <p className="text-sm text-accent-primary">Uploading…</p>}
          </div>
        );
      case 5:
        return (
          <div className="space-y-4">
            <Field label="Email">
              <input className={inputClass()} readOnly value={form.contact.email} />
            </Field>
            <div className="flex gap-2 items-end">
              <Field label="Phone" required>
                <div className="flex gap-2">
                  <input className={`${inputClass()} w-24`} value={form.contact.phone_country_code} onChange={(e) => patch('contact', 'phone_country_code', e.target.value)} />
                  <input className={inputClass()} value={form.contact.phone_number} onChange={(e) => patch('contact', 'phone_number', e.target.value)} placeholder="82 123 4567" />
                </div>
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.declarations.accurate_information_declaration} onChange={(e) => patch('declarations', 'accurate_information_declaration', e.target.checked)} />
              I declare that all information provided is true and complete
            </label>
            <div className="bg-gray-50 rounded-lg p-4 text-left text-sm space-y-1">
              <p><strong>Name:</strong> {form.personal.legal_first_name} {form.personal.legal_last_name}</p>
              <p><strong>ID:</strong> {form.identity.document_type} — {form.identity.document_number}</p>
              <p><strong>Address:</strong> {form.address.street_line_1}, {form.address.city}</p>
              <p><strong>Risk:</strong> {form.trading.risk_appetite}</p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-main-bg p-4 font-body flex justify-center">
      <div className="bg-card-bg rounded-xl shadow-xl w-full max-w-3xl p-8">
        <h1 className="text-2xl font-bold text-text-primary font-display">KYC Verification</h1>
        <p className="text-text-secondary text-sm mt-1 mb-4">
          {demoMode ? 'Demo mode — submission is simulated.' : `Profile completion: ${completion}%`}
          {saving && <span className="ml-2 text-accent-primary">Saving…</span>}
        </p>
        <div className="flex gap-1 mb-6 overflow-x-auto">
          {STEPS.map((name, i) => (
            <button
              key={name}
              type="button"
              onClick={() => setStep(i)}
              className={`px-2 py-1 text-[10px] font-mono rounded whitespace-nowrap ${i === step ? 'bg-accent-primary text-white' : 'bg-input-bg text-text-secondary'}`}
            >
              {i + 1}. {name}
            </button>
          ))}
        </div>
        {error && <p className="text-red-600 text-sm mb-4 p-2 bg-red-50 rounded">{error}</p>}
        <div className="min-h-[320px]">{renderStep()}</div>
        <div className="flex justify-between mt-8 gap-3">
          <button type="button" onClick={back} disabled={step === 0} className="px-4 py-2 border rounded-lg disabled:opacity-40">Back</button>
          {step < STEPS.length - 1 ? (
            <button type="button" onClick={next} className="px-6 py-2 bg-accent-primary text-white rounded-lg font-semibold">Continue</button>
          ) : (
            <button type="button" onClick={submit} disabled={submitting} className="px-6 py-2 bg-accent-primary text-white rounded-lg font-semibold disabled:opacity-50">
              {submitting ? 'Submitting…' : 'Submit KYC'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
