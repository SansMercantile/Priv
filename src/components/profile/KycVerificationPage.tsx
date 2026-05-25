import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/apiClient';
import { ShieldCheck, UploadCloud, AlertCircle, ArrowLeft, ArrowRight, Save, Landmark } from 'lucide-react';

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
  { value: 'passport', label: 'Passport Document' },
  { value: 'national_id', label: 'National Identity Card' },
  { value: 'drivers_license', label: "Driver's Licence" },
  { value: 'residence_permit', label: 'Permanent Residence Permit' },
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
    products_traded: [] as string[],
    risk_appetite: '',
    investment_objectives: [] as string[],
  },
  tax: {
    tax_residency_country: '',
    tax_identification_number: '',
    us_person_fatca: false,
    fatca_declaration_acknowledged: false,
  },
  contact: {
    email: '',
    email_verified: true,
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

function Field({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <label className="block text-sm">
      <span className="text-zinc-200 font-medium font-mono text-xs tracking-wide">
        {label}
        {required && <span className="text-rose-500 ml-1">*</span>}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

function inputClass() {
  return 'w-full p-3 rounded-lg bg-zinc-900/90 text-white border border-zinc-800 focus:outline-none focus:ring-1 focus:ring-rose-500/50 focus:border-rose-500/50 transition duration-150 text-sm font-mono';
}

interface KycVerificationPageProps {
  demoMode?: boolean;
  onSuccess?: () => void;
}

export default function KycVerificationPage({ demoMode = false, onSuccess }: KycVerificationPageProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [uploads, setUploads] = useState<Record<string, { filename: string; document_type: string; url?: string }>>({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completion, setCompletion] = useState(0);

  useEffect(() => {
    // Attempt to pull user email from memory or demo session
    const savedEmail = localStorage.getItem("xm_account_email") || "client@merchant.priv";
    setForm((f) => ({
      ...f,
      contact: { ...f.contact, email: savedEmail, email_verified: true },
    }));
  }, []);

  useEffect(() => {
    if (demoMode) {
      // Load local mock form if any
      const savedDraft = localStorage.getItem("kyc_draft_demo");
      if (savedDraft) {
        try {
          setForm(JSON.parse(savedDraft));
        } catch (_) {}
      }
      return;
    }
    
    (async () => {
      try {
        const data = await apiClient.getKycRecord();
        if (data && data.personal) {
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
        setCompletion(st?.completion_percent ?? 0);
      } catch (e) {
        console.warn('KYC load failed:', e);
      }
    })();
  }, [demoMode]);

  const patch = (section: string, field: string, value: any) => {
    setForm((f) => ({ ...f, [section]: { ...(f as any)[section], [field]: value } }));
    
    // Auto-save temporary state in demo mode
    if (demoMode) {
      const updated = { ...form, [section]: { ...(form as any)[section], [field]: value } };
      localStorage.setItem("kyc_draft_demo", JSON.stringify(updated));
    }
  };

  const saveDraft = useCallback(async () => {
    if (demoMode) {
      localStorage.setItem("kyc_draft_demo", JSON.stringify(form));
      localStorage.setItem("xm_kyc_status", "draft");
      return;
    }
    setSaving(true);
    try {
      await apiClient.saveKycDraft(form);
      const st = await apiClient.getKycStatus();
      setCompletion(st?.completion_percent ?? 0);
    } catch (e) {
      console.warn('Draft save failed', e);
    } finally {
      setSaving(false);
    }
  }, [demoMode, form]);

  const handleUpload = async (file: File | null, docType: string) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      if (demoMode) {
        setUploads((u) => ({ ...u, [docType]: { filename: file.name, document_type: docType, url: URL.createObjectURL(file) } }));
      } else {
        const res = await apiClient.submitKYCDocument(file, docType);
        const uploadedData = res.data;
        setUploads((u) => ({ ...u, [docType]: { filename: uploadedData.filename, document_type: uploadedData.document_type, url: uploadedData.url } }));
      }
    } catch (e: any) {
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
    
    const formattedPayload = {
      ...form,
      fullName: `${form.personal.legal_first_name} ${form.personal.legal_last_name}`,
      dob: form.personal.date_of_birth,
      nationality: form.personal.nationality,
      documentType: form.identity.document_type,
      documentNumber: form.identity.document_number,
      incomeRange: form.financial.annual_income_range || '< R50k',
      netWorthRange: form.financial.net_worth_range || '< R50k',
      tradingExperience: form.trading.years_trading_experience || 'None',
      documents: Object.entries(uploads).map(([type, doc]) => ({
        type,
        url: doc.url || '#',
        filename: doc.filename
      }))
    };

    if (demoMode) {
      // Write locally as submitted application for KycAdminReviewPage to pull
      localStorage.setItem("xm_kyc_status", "submitted");
      
      const savedAppsStr = localStorage.getItem("kyc_applications_queue") || "[]";
      try {
        const currentList = JSON.parse(savedAppsStr);
        // Create matching model to show up in Admin Review Page
        const newApp = {
          id: `KYC-DEMO-${Date.now()}`,
          fullName: formattedPayload.fullName,
          email: form.contact.email,
          dob: formattedPayload.dob,
          nationality: formattedPayload.nationality,
          documentType: formattedPayload.documentType,
          documentNumber: formattedPayload.documentNumber,
          incomeRange: formattedPayload.incomeRange,
          netWorthRange: formattedPayload.netWorthRange,
          tradingExperience: formattedPayload.tradingExperience,
          submittedAt: new Date().toLocaleDateString('en-US', { hour: '2-digit', minute: '2-digit' }),
          status: 'pending',
          documents: formattedPayload.documents.length > 0 ? formattedPayload.documents : [
            { type: 'ID / Passport - Front', url: '#', filename: 'passport_scan.png' },
            { type: 'Proof of Residency', url: '#', filename: 'bank_statement.pdf' }
          ]
        };
        currentList.push(newApp);
        localStorage.setItem("kyc_applications_queue", JSON.stringify(currentList));
      } catch (_) {}

      setTimeout(() => {
        setSubmitting(false);
        if (onSuccess) {
          onSuccess();
        } else {
          navigate('/dashboard');
        }
      }, 1200);
      return;
    }
    try {
      await apiClient.submitKyc(formattedPayload);
      localStorage.setItem("xm_kyc_status", "submitted");
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/dashboard');
      }
    } catch (e: any) {
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
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
              <input type="date" className={inputClass()} value={form.personal.date_of_birth} onChange={(e) => patch('personal', 'date_of_birth', e.target.value)} style={{ colorScheme: "dark" }} />
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
            <div className="grid grid-cols-2 gap-3 md:col-span-1">
              <Field label="Issue date">
                <input type="date" className={inputClass()} value={form.identity.issue_date} onChange={(e) => patch('identity', 'issue_date', e.target.value)} style={{ colorScheme: "dark" }} />
              </Field>
              <Field label="Expiry date">
                <input type="date" className={inputClass()} value={form.identity.expiry_date} onChange={(e) => patch('identity', 'expiry_date', e.target.value)} style={{ colorScheme: "dark" }} />
              </Field>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <div className="md:col-span-2">
              <Field label="Street address line 1" required>
                <input className={inputClass()} value={form.address.street_line_1} onChange={(e) => patch('address', 'street_line_1', e.target.value)} placeholder="e.g. 42 Sovereign Trade Boulevard" />
              </Field>
            </div>
            <div className="md:col-span-2">
              <Field label="Street line 2">
                <input className={inputClass()} value={form.address.street_line_2} onChange={(e) => patch('address', 'street_line_2', e.target.value)} placeholder="Apartment, block, suite" />
              </Field>
            </div>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <Field label="Employment status" required>
              <select className={inputClass()} value={form.financial.employment_status} onChange={(e) => patch('financial', 'employment_status', e.target.value)}>
                <option value="">Select status</option>
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
                <option value="">Select origin</option>
                <option value="salary">Salary / Remuneration</option>
                <option value="business">Business profits</option>
                <option value="investments">Investments</option>
                <option value="inheritance">Inheritance</option>
                <option value="savings">Savings</option>
              </select>
            </Field>
            <Field label="Annual income range">
              <select className={inputClass()} value={form.financial.annual_income_range} onChange={(e) => patch('financial', 'annual_income_range', e.target.value)}>
                <option value="">Select range</option>
                {INCOME_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Net worth range">
              <select className={inputClass()} value={form.financial.net_worth_range} onChange={(e) => patch('financial', 'net_worth_range', e.target.value)}>
                <option value="">Select range</option>
                {INCOME_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Years trading experience" required>
              <select className={inputClass()} value={form.trading.years_trading_experience} onChange={(e) => patch('trading', 'years_trading_experience', e.target.value)}>
                <option value="">Select experience</option>
                {EXPERIENCE.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Trading knowledge" required>
              <select className={inputClass()} value={form.trading.trading_knowledge_level} onChange={(e) => patch('trading', 'trading_knowledge_level', e.target.value)}>
                <option value="">Select level</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="professional">Professional</option>
              </select>
            </Field>
            <div className="md:col-span-2">
              <Field label="Risk appetite" required>
                <select className={inputClass()} value={form.trading.risk_appetite} onChange={(e) => patch('trading', 'risk_appetite', e.target.value)}>
                  <option value="">Select tolerance</option>
                  {RISK_LEVELS.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </Field>
            </div>
            <div className="md:col-span-2 mt-2 p-3 bg-zinc-950 rounded border border-zinc-850 flex items-start gap-3">
              <input
                type="checkbox"
                id="isPEP"
                className="mt-1 w-4 h-4 text-rose-600 bg-zinc-900 border-zinc-800 rounded focus:ring-rose-500"
                checked={form.financial.is_politically_exposed}
                onChange={(e) => patch('financial', 'is_politically_exposed', e.target.checked)}
              />
              <label htmlFor="isPEP" className="text-xs text-zinc-300 leading-normal font-mono">
                <strong>Political Exposure:</strong> I declare that I am, or have been associated with, a Politically Exposed Person (PEP).
              </label>
            </div>
            {form.financial.is_politically_exposed && (
              <div className="md:col-span-2">
                <Field label="Describe official duties / associations" required>
                  <textarea className={inputClass()} rows={3} value={form.financial.pep_details} onChange={(e) => patch('financial', 'pep_details', e.target.value)} placeholder="Provide timeline and official responsibilities..." />
                </Field>
              </div>
            )}
          </div>
        );
      case 3:
        return (
          <div className="space-y-6 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Field label="Tax residency country" required>
                <input className={inputClass()} value={form.tax.tax_residency_country} onChange={(e) => patch('tax', 'tax_residency_country', e.target.value)} />
              </Field>
              <Field label="Tax ID / TRN">
                <input className={inputClass()} value={form.tax.tax_identification_number} onChange={(e) => patch('tax', 'tax_identification_number', e.target.value)} placeholder="e.g. 19-328-103" />
              </Field>
            </div>
            <div className="space-y-3.5 bg-zinc-900/60 p-4 rounded-xl border border-zinc-800">
              <h3 className="text-[#e11d48] font-mono text-xs uppercase tracking-widest font-semibold flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" /> Compliance Attestation (Sovereign Trust Framework)
              </h3>
              <div className="space-y-3 mt-3">
                {[
                  { section: 'tax', field: 'us_person_fatca', text: 'I am a US person (citizen, resident, green card) for FATCA compliance' },
                  { section: 'tax', field: 'fatca_declaration_acknowledged', text: 'I acknowledge the FATCA / CRS reporting policies' },
                  { section: 'declarations', field: 'terms_accepted', text: 'I accept the general SANS Mercantile Terms of Execution' },
                  { section: 'declarations', field: 'privacy_accepted', text: 'I consent to the processing of identity profiles in alignment with localized privacy rules' },
                  { section: 'declarations', field: 'aml_consent', text: 'I voluntarily submit to AML/CTF automated screenings' },
                  { section: 'declarations', field: 'sanctions_screening_consent', text: 'I consent to regular global sanctions database verification' }
                ].map(({ section, field, text }) => (
                  <label key={field} className="flex items-start gap-3 cursor-pointer group">
                    <input
                      type="checkbox"
                      className="mt-0.5 w-4.5 h-4.5 text-rose-600 bg-zinc-950 border-zinc-800 rounded focus:ring-rose-500/50"
                      checked={(form as any)[section][field]}
                      onChange={(e) => patch(section, field, e.target.checked)}
                    />
                    <span className="text-xs text-zinc-300 font-mono group-hover:text-white transition duration-150">
                      {text}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-5 mt-4">
            <div className="bg-zinc-950/80 p-4 rounded-lg border border-zinc-800/60 text-xs font-mono text-zinc-400 leading-relaxed flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <span>
                To fully establish a live algorithmic connection and bypass delayed indicators, you must upload clear, legible color copies of your credentials (PNG, JPG, or PDF. Max 10MB per file).
              </span>
            </div>
            {[
              { key: 'id_front', label: 'Government Passport or National Identity Code (Front/Profile Page)', desc: 'Must display photo, registration ID, birthday, and expiration clearly.' },
              { key: 'id_back', label: 'National ID card (Backside - if applicable)', desc: 'Submit only if a back side exists and contains barcodes / signatures.' },
              { key: 'proof_of_address', label: 'Proof of sovereign residence (Utility bill, local tax assessment < 3 months)', desc: 'Name and physical address match form values exactly.' },
              { key: 'selfie', label: 'Biometric selfie validation', desc: 'Secure desktop or smartphone camera portrait focusing on facial traits.' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="border border-zinc-800 bg-zinc-950/60 rounded-xl p-4 transition-all hover:bg-zinc-950 duration-200">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2">
                  <div>
                    <p className="font-mono text-xs font-bold text-white uppercase tracking-wide">{label}</p>
                    <p className="text-[10px] text-zinc-400 mt-0.5 font-light">{desc}</p>
                  </div>
                  <div className="relative">
                    <input
                      type="file"
                      id={`file-${key}`}
                      className="hidden"
                      accept="image/jpeg,image/png,application/pdf"
                      onChange={(e) => handleUpload(e.target.files ? e.target.files[0] : null, key)}
                    />
                    <label
                      htmlFor={`file-${key}`}
                      className="px-3.5 py-1.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white rounded text-[11px] font-mono text-zinc-300 font-bold flex items-center gap-1.5 cursor-pointer transition"
                    >
                      <UploadCloud className="w-3.5 h-3.5" /> Upload File
                    </label>
                  </div>
                </div>
                {uploads[key] && (
                  <div className="flex items-center gap-2 mt-2 p-2 bg-zinc-900/50 rounded border border-rose-500/20">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <p className="text-[11px] text-zinc-300 font-mono truncate max-w-xs">
                      Document synced: <strong>{uploads[key].filename}</strong>
                    </p>
                  </div>
                )}
              </div>
            ))}
            {uploading && <p className="text-xs font-mono text-rose-500 animate-pulse">Syncing encrypted document payload with SANS node vaults...</p>}
          </div>
        );
      case 5:
        return (
          <div className="space-y-5 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Field label="Registered verification email">
                <input className="w-full p-3 rounded-lg bg-zinc-950 text-zinc-500 border border-zinc-900 cursor-not-allowed text-sm font-mono" readOnly value={form.contact.email} />
              </Field>
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <Field label="Phone / Mobile contact" required>
                    <div className="flex gap-2">
                      <input className={`${inputClass()} w-24`} value={form.contact.phone_country_code} onChange={(e) => patch('contact', 'phone_country_code', e.target.value)} />
                      <input className={inputClass()} value={form.contact.phone_number} onChange={(e) => patch('contact', 'phone_number', e.target.value)} placeholder="082 123 4567" />
                    </div>
                  </Field>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-zinc-950 rounded border border-zinc-850 flex items-start gap-3 mt-4">
              <input
                type="checkbox"
                id="accurateDeclaration"
                className="mt-1 w-4 h-4 text-rose-600 bg-zinc-900 border-zinc-800 rounded focus:ring-rose-500"
                checked={form.declarations.accurate_information_declaration}
                onChange={(e) => patch('declarations', 'accurate_information_declaration', e.target.checked)}
              />
              <label htmlFor="accurateDeclaration" className="text-[11px] text-zinc-300 leading-relaxed font-mono">
                <strong>Solemn Attestation:</strong> I declare under penalty of perjury that all details and uploaded files correspond strictly to my legal, true, and active personal assets, accounts, and residential status.
              </label>
            </div>

            <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-2 mt-4 text-xs font-mono">
              <p className="text-[#e11d48] uppercase font-bold text-[10px] tracking-widest border-b border-zinc-850 pb-1.5">PREVIEW SUBMISSION DOSSIER</p>
              <p className="text-zinc-400"><strong>Contract Owner:</strong> <span className="text-white">{form.personal.legal_first_name} {form.personal.legal_last_name || 'N/A'}</span></p>
              <p className="text-zinc-400"><strong>Identity Code:</strong> <span className="text-white uppercase">{form.identity.document_type}</span> : {form.identity.document_number || 'N/A'}</p>
              <p className="text-zinc-400"><strong>Billing Address:</strong> <span className="text-white">{form.address.street_line_1}, {form.address.city || 'N/A'} ({form.address.country || 'N/A'})</span></p>
              <p className="text-zinc-400"><strong>Aggressive Risk profile:</strong> <span className="text-rose-400 font-bold uppercase">{form.trading.risk_appetite || 'N/A'}</span></p>
              <p className="text-zinc-400"><strong>Targeting asset lines:</strong> <span className="text-white font-bold">{uploads['id_front'] ? 'Bio documentation attached' : 'No biometric page files linked yet'}</span></p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-1 min-h-[500px] flex items-center justify-center font-sans">
      <div className="bg-zinc-950/30 border border-zinc-800/40 rounded-xl shadow-2xl w-full p-4 sm:p-6 backdrop-blur-md">
        
        {/* Progress Bar & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-900 pb-4 mb-5 gap-3">
          <div>
            <h2 className="text-lg font-serif italic text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-rose-500" /> SANS AML Compliance Dossier
            </h2>
            <p className="text-[10px] text-zinc-400 font-mono mt-1 font-light">
              {demoMode ? 'PROVISIONAL SANDBOX SESSION' : `Secure Ledger completion score: ${completion}%`}
              {saving && <span className="ml-2 text-rose-500 font-bold">&#10022; Saving draft indicators...</span>}
            </p>
          </div>
          
          {/* Quick Step Indicators */}
          <div className="flex items-center gap-1 font-mono text-[9px]">
            <span className="px-2 py-1 bg-rose-950/40 text-rose-400 font-bold border border-rose-900/50 rounded-md">
              SECURE STAGE {step + 1} / {STEPS.length}
            </span>
          </div>
        </div>

        {/* Steps Navigation Rail */}
        <div className="flex gap-1 mb-6 overflow-x-auto scrollbar-hide py-1">
          {STEPS.map((name, i) => (
            <button
              key={name}
              type="button"
              onClick={() => setStep(i)}
              className={`px-2.5 py-1 text-[9px] font-mono rounded-md whitespace-nowrap border transition duration-150 ${
                i === step 
                  ? 'bg-rose-950/40 text-rose-400 border-rose-500/30 font-bold' 
                  : 'bg-zinc-900/20 text-zinc-500 border-zinc-800/40 hover:text-zinc-200'
              }`}
            >
              {i + 1}. {name}
            </button>
          ))}
        </div>

        {/* Errors indicator */}
        {error && (
          <div className="text-rose-400 text-xs font-mono mb-5 p-3 bg-rose-950/20 rounded border border-rose-500/30 flex items-start gap-2.5">
            <AlertCircle className="w-4.5 h-4.5 text-rose-500 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Step Container */}
        <div className="min-h-[300px] border border-zinc-850 bg-zinc-900/10 p-5 rounded-xl">
          {renderStep()}
        </div>

        {/* Action Controls */}
        <div className="flex justify-between items-center mt-7 gap-3">
          <button
            type="button"
            onClick={back}
            disabled={step === 0}
            className="px-4 py-2 border border-zinc-800 bg-zinc-950 text-zinc-300 font-mono text-[11px] rounded-lg disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-900 hover:text-white transition flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Prev Step
          </button>
          
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={saveDraft}
              disabled={saving}
              className="px-3 py-2 border border-zinc-800 bg-zinc-950 text-zinc-400 font-mono text-[11px] rounded-lg hover:bg-zinc-900 hover:text-white transition flex items-center gap-1"
              title="Save temporary draft progress to workspace session"
            >
              <Save className="w-3.5 h-3.5" /> Save Progress
            </button>
            
            {step < STEPS.length - 1 ? (
              <button
                type="button"
                onClick={next}
                className="px-4 py-2 bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 hover:text-white rounded-lg font-bold font-mono text-[11px] text-zinc-200 transition flex items-center gap-1.5 animate-pulse"
              >
                Continue <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={submit}
                disabled={submitting || !form.declarations.accurate_information_declaration}
                className="px-5 py-2 bg-[#e11d48] hover:bg-rose-500 text-white border border-rose-500/20 font-bold font-mono text-[11px] rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(225,29,72,0.25)]"
              >
                {submitting ? 'Transmitting...' : 'Dispatch AML Dossier'}
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
