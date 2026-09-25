import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/apiClient';
import {
  ShieldCheck, UploadCloud, AlertCircle, ArrowLeft, ArrowRight,
  Save, Camera, CheckCircle, XCircle, Loader2, MapPin,
} from 'lucide-react';

// ─── Country / Tax data ───────────────────────────────────────────────────────
const COUNTRIES = [
  { code: 'ZA', name: 'South Africa',    tinLabel: 'Tax Reference Number (TRN)',    tinFormat: '9 digits e.g. 1234567890',  fatcaRelevant: false },
  { code: 'US', name: 'United States',   tinLabel: 'SSN or EIN',                   tinFormat: 'ddd-dd-dddd',               fatcaRelevant: true  },
  { code: 'GB', name: 'United Kingdom',  tinLabel: 'UTR / National Insurance No.',  tinFormat: 'e.g. 1234567890 or QQ123456C', fatcaRelevant: false },
  { code: 'DE', name: 'Germany',         tinLabel: 'Steueridentifikationsnummer',   tinFormat: '11 digits',                 fatcaRelevant: false },
  { code: 'FR', name: 'France',          tinLabel: 'Numéro Fiscal (NIF)',           tinFormat: '13 digits',                 fatcaRelevant: false },
  { code: 'AE', name: 'UAE',             tinLabel: 'TIN (if registered)',           tinFormat: 'Optional for individuals',  fatcaRelevant: false },
  { code: 'AU', name: 'Australia',       tinLabel: 'Tax File Number (TFN)',         tinFormat: 'ddd ddd ddd',               fatcaRelevant: false },
  { code: 'CA', name: 'Canada',          tinLabel: 'Social Insurance Number (SIN)', tinFormat: 'ddd-ddd-ddd',              fatcaRelevant: false },
  { code: 'IN', name: 'India',           tinLabel: 'Permanent Account Number (PAN)', tinFormat: 'AAAAA9999A',              fatcaRelevant: false },
  { code: 'SG', name: 'Singapore',       tinLabel: 'NRIC / FIN',                   tinFormat: 'S/T/F/G + 7 digits + letter', fatcaRelevant: false },
  { code: 'NG', name: 'Nigeria',         tinLabel: 'Tax Identification Number',     tinFormat: 'dd-dddddddd-dddd',          fatcaRelevant: false },
  { code: 'KE', name: 'Kenya',           tinLabel: 'PIN Certificate No.',           tinFormat: 'A + 9 digits + Z',          fatcaRelevant: false },
  { code: 'NL', name: 'Netherlands',     tinLabel: 'BSN (Burgerservicenummer)',      tinFormat: '9 digits',                  fatcaRelevant: false },
  { code: 'CH', name: 'Switzerland',     tinLabel: 'AHV / UID',                    tinFormat: '756.XXXX.XXXX.XX',          fatcaRelevant: false },
  { code: 'OTHER', name: 'Other',        tinLabel: 'Tax ID / TRN',                  tinFormat: '',                          fatcaRelevant: false },
];

const STEPS = ['Legal & Identity', 'Address', 'Financial & Trading', 'Tax & Compliance', 'Documents', 'Review & Submit'];
const INCOME_RANGES = ['< R50k', 'R50k–R200k', 'R200k–R500k', 'R500k–R1m', '> R1m'];
const EXPERIENCE    = ['None', '< 1 year', '1–3 years', '3–5 years', '5+ years'];
const RISK_LEVELS   = ['Conservative', 'Moderate', 'Aggressive', 'Very aggressive'];
const DOC_TYPES     = [
  { value: 'passport',         label: 'Passport Document' },
  { value: 'national_id',      label: 'National Identity Card' },
  { value: 'drivers_license',  label: "Driver's Licence" },
  { value: 'residence_permit', label: 'Permanent Residence Permit' },
];

const emptyForm = () => ({
  personal: { legal_first_name: '', legal_middle_name: '', legal_last_name: '', date_of_birth: '', gender: '', nationality: '', country_of_residence: '', place_of_birth: '' },
  identity:  { document_type: 'passport', document_number: '', issuing_country: '', issue_date: '', expiry_date: '' },
  address:   { street_line_1: '', street_line_2: '', city: '', province_state: '', postal_code: '', country: '', verified: false },
  financial: { employment_status: '', employer_name: '', occupation: '', source_of_funds: '', annual_income_range: '', net_worth_range: '', is_politically_exposed: false, pep_details: '' },
  trading:   { years_trading_experience: '', trading_knowledge_level: '', risk_appetite: '' },
  tax: { tax_residency_countries: [] as string[], tax_identification_number: '', has_no_tax_number: false, us_person_fatca: false, fatca_declaration_acknowledged: false },
  contact: { email: '', phone_country_code: '+27', phone_number: '' },
  declarations: { terms_accepted: false, privacy_accepted: false, aml_consent: false, sanctions_screening_consent: false, accurate_information_declaration: false },
});

// ─── Sub-components ───────────────────────────────────────────────────────────
function Field({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <label className="block text-sm">
      <span className="text-zinc-200 font-medium font-mono text-xs tracking-wide">
        {label}{required && <span className="text-rose-500 ml-1">*</span>}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
const ic = () => 'w-full p-3 rounded-lg bg-zinc-900/90 text-white border border-zinc-800 focus:outline-none focus:ring-1 focus:ring-rose-500/50 focus:border-rose-500/50 transition text-sm font-mono';
const sc = () => `${ic()} cursor-pointer`;

// ─── Google Maps address autocomplete hook ────────────────────────────────────
function useGoogleMapsAutocomplete(
  inputRef: React.RefObject<HTMLInputElement>,
  onPlace: (place: google.maps.places.PlaceResult) => void
) {
  useEffect(() => {
    const apiKey = (window as any).__GOOGLE_MAPS_KEY__ || (import.meta as any).env?.VITE_GOOGLE_MAPS_KEY;
    if (!apiKey || !(window as any).google?.maps?.places) {
      // Load Google Maps script if not present
      if (apiKey && !document.getElementById('gmaps-script')) {
        const s = document.createElement('script');
        s.id = 'gmaps-script';
        s.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
        s.async = true;
        s.onload = () => initAC();
        document.head.appendChild(s);
      }
      return;
    }
    initAC();

    function initAC() {
      if (!inputRef.current || !(window as any).google?.maps?.places) return;
      const ac = new (window as any).google.maps.places.Autocomplete(inputRef.current, {
        types: ['address'],
      });
      ac.addListener('place_changed', () => onPlace(ac.getPlace()));
    }
  }, [inputRef, onPlace]);
}

// ─── Face Camera Modal ────────────────────────────────────────────────────────
function FaceCameraModal({
  onCapture,
  onClose,
}: {
  onCapture: (base64: string) => void;
  onClose: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
      .then((stream) => {
        if (videoRef.current) { videoRef.current.srcObject = stream; setStreaming(true); }
      })
      .catch((e) => setError(`Camera error: ${e.message}`));
    return () => {
      if (videoRef.current?.srcObject) {
        (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext('2d')!;
    canvasRef.current.width = videoRef.current.videoWidth;
    canvasRef.current.height = videoRef.current.videoHeight;
    ctx.drawImage(videoRef.current, 0, 0);
    const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.85);
    const base64 = dataUrl.split(',')[1];
    // Stop stream
    (videoRef.current.srcObject as MediaStream)?.getTracks().forEach(t => t.stop());
    onCapture(base64);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-mono text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            <Camera className="w-4 h-4 text-rose-500" /> Biometric Face Verification
          </h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-white text-xs font-mono">[CLOSE]</button>
        </div>
        {error ? (
          <div className="text-rose-400 text-xs font-mono p-3 bg-rose-950/20 rounded">{error}</div>
        ) : (
          <>
            <div className="relative rounded-xl overflow-hidden border border-zinc-800 bg-black">
              <video ref={videoRef} autoPlay playsInline className="w-full rounded-xl" />
              {/* Face guide overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-48 h-60 border-2 border-rose-500/60 rounded-full opacity-70" style={{ borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%' }} />
              </div>
            </div>
            <canvas ref={canvasRef} className="hidden" />
            <p className="text-zinc-500 text-xs font-mono mt-3 text-center">
              Centre your face within the oval. Ensure even lighting and look directly at camera.
            </p>
            <button
              onClick={capture}
              disabled={!streaming}
              className="mt-4 w-full py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold font-mono text-sm rounded-xl disabled:opacity-30 transition flex items-center justify-center gap-2"
            >
              <Camera className="w-4 h-4" /> Capture Verification Photo
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Document AI Verify Badge ─────────────────────────────────────────────────
function VerifyBadge({ result }: { result: any }) {
  if (!result) return null;
  const ok = result.verified || result.match;
  return (
    <div className={`mt-2 p-2 rounded-lg border text-[10px] font-mono flex items-center gap-2 ${ok ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-400' : 'bg-amber-950/30 border-amber-800/50 text-amber-400'}`}>
      {ok ? <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" /> : <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />}
      <span>AI: {result.notes || (ok ? 'Verified' : 'Needs review')} — confidence {result.confidence ?? '?'}%</span>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
interface KycVerificationPageProps { demoMode?: boolean; onSuccess?: () => void; }

export default function KycVerificationPage({ demoMode = false, onSuccess }: KycVerificationPageProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [uploads, setUploads] = useState<Record<string, { filename: string; url?: string; base64?: string; mimeType?: string }>>({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completion, setCompletion] = useState(0);
  const [showCamera, setShowCamera] = useState(false);
  const [selfieBase64, setSelfieBase64] = useState<string | null>(null);
  const [faceVerifyResult, setFaceVerifyResult] = useState<any>(null);
  const [docVerifyResults, setDocVerifyResults] = useState<Record<string, any>>({});
  const [verifyingDoc, setVerifyingDoc] = useState<string | null>(null);
  const [addressVerified, setAddressVerified] = useState(false);
  const addressInputRef = useRef<HTMLInputElement>(null);
  // Outstanding-items popup: listing of required (*) fields still empty.
  const [outstanding, setOutstanding] = useState<Array<{ label: string; step: number }> | null>(null);

  // Every *-marked field must be filled before dispatch. Returns the
  // missing items with their step so the popup can jump straight there.
  const validateAll = (): Array<{ label: string; step: number }> => {
    const missing: Array<{ label: string; step: number }> = [];
    const need = (cond: any, label: string, step: number) => {
      if (!cond) missing.push({ label, step });
    };
    const p = form.personal, id = form.identity, a = form.address;
    const f = form.financial, t = form.trading, tx = form.tax, d = form.declarations;
    need(p.legal_first_name?.trim(), "Legal first name", 0);
    need(p.legal_last_name?.trim(), "Legal last name", 0);
    need(p.date_of_birth, "Date of birth", 0);
    need(p.nationality?.trim(), "Nationality", 0);
    need(p.country_of_residence, "Country of residence", 0);
    need(id.document_number?.trim(), "Document number", 0);
    need(id.issuing_country, "Issuing country", 0);
    need(a.street_line_1?.trim(), "Street address", 1);
    need(a.city?.trim(), "City", 1);
    need(a.country, "Address country", 1);
    need(form.contact.phone_number?.trim(), "Phone number", 5);
    need(f.employment_status, "Employment status", 2);
    need(f.source_of_funds, "Source of funds", 2);
    need(t.years_trading_experience, "Trading experience", 2);
    need(t.trading_knowledge_level, "Knowledge level", 2);
    need(t.risk_appetite, "Risk appetite", 2);
    if (f.is_politically_exposed) need(f.pep_details?.trim(), "PEP duties / associations", 2);
    need((tx.tax_residency_countries || []).length > 0, "Tax residency country", 3);
    if (!tx.has_no_tax_number) need(tx.tax_identification_number?.trim(), "Tax identification number (or tick 'no tax number')", 3);
    if (needsFatca) need(tx.fatca_declaration_acknowledged, "FATCA / CRS acknowledgement", 3);
    need(d.terms_accepted, "Terms of Execution acceptance", 3);
    need(d.privacy_accepted, "Privacy consent", 3);
    need(d.aml_consent, "AML/CTF screening consent", 3);
    need(d.sanctions_screening_consent, "Sanctions screening consent", 3);
    need(uploads['id_front'], "Government ID / Passport (front) upload", 4);
    // Back side mandatory only for card-type documents with two sides.
    // Passports carry everything on the front.
    if (['national_id', 'drivers_license', 'residence_permit'].includes(id.document_type)) {
      need(uploads['id_back'], "ID card back upload (required for card documents)", 4);
    }
    need(uploads['proof_of_address'], "Proof of residence upload (< 3 months)", 4);
    need(selfieBase64, "Biometric selfie capture", 4);
    need(d.accurate_information_declaration, "Perjury declaration checkbox", 5);
    return missing;
  };

  // Selected tax countries info
  const selectedTaxCountries = (form.tax.tax_residency_countries || [])
    .map(code => COUNTRIES.find(c => c.code === code))
    .filter(Boolean) as typeof COUNTRIES;
  const needsFatca = selectedTaxCountries.some(c => c.fatcaRelevant);

  // Google Maps autocomplete
  useGoogleMapsAutocomplete(addressInputRef as any, (place) => {
    const comps = place.address_components || [];
    const get = (type: string) => comps.find(c => c.types.includes(type))?.long_name || '';
    const getShort = (type: string) => comps.find(c => c.types.includes(type))?.short_name || '';
    patch('address', 'street_line_1', `${get('street_number')} ${get('route')}`.trim());
    patch('address', 'city', get('locality') || get('sublocality'));
    patch('address', 'province_state', get('administrative_area_level_1'));
    patch('address', 'postal_code', get('postal_code'));
    patch('address', 'country', get('country'));
    patch('address', 'verified', true);
    setAddressVerified(true);
  });

  useEffect(() => {
    const email = localStorage.getItem('xm_account_email') || '';
    setForm(f => ({ ...f, contact: { ...f.contact, email } }));
  }, []);

  useEffect(() => {
    if (demoMode) {
      const draft = localStorage.getItem('kyc_draft_demo');
      if (draft) { try { setForm(JSON.parse(draft)); } catch (_) {} }
      return;
    }
    (async () => {
      try {
        const data = await apiClient.getKycRecord();
        if (data?.personal) setForm(f => ({ ...f, ...data }));
        const st = await apiClient.getKycStatus();
        setCompletion(st?.completion_percent ?? 0);
      } catch (e) { console.warn('KYC load:', e); }
    })();
  }, [demoMode]);

  const patch = (section: string, field: string, value: any) =>
    setForm(f => ({ ...f, [section]: { ...(f as any)[section], [field]: value } }));

  const saveDraft = useCallback(async () => {
    if (demoMode) { localStorage.setItem('kyc_draft_demo', JSON.stringify(form)); return; }
    setSaving(true);
    try { await apiClient.saveKycDraft(form); } catch (e) { console.warn(e); } finally { setSaving(false); }
  }, [demoMode, form]);

  const handleUpload = async (file: File | null, docKey: string) => {
    if (!file) return;
    setUploading(true); setError(null);
    try {
      const url = URL.createObjectURL(file);
      // Convert to base64 for AI verification
      const base64 = await new Promise<string>((res, rej) => {
        const r = new FileReader();
        r.onload = () => res((r.result as string).split(',')[1]);
        r.onerror = rej;
        r.readAsDataURL(file);
      });
      setUploads(u => ({ ...u, [docKey]: { filename: file.name, url, base64, mimeType: file.type } }));

      // Trigger AI document verification in background
      if (!demoMode && docKey.startsWith('id_')) {
        setVerifyingDoc(docKey);
        try {
          const result = await apiClient.verifyDocument(base64, file.type, {
            fullName: `${form.personal.legal_first_name} ${form.personal.legal_last_name}`,
            dob: form.personal.date_of_birth,
            documentNumber: form.identity.document_number,
            documentType: form.identity.document_type,
            issuingCountry: form.identity.issuing_country,
          });
          setDocVerifyResults(r => ({ ...r, [docKey]: result }));
        } catch (e) { console.warn('Doc verify:', e); }
        finally { setVerifyingDoc(null); }
      }
    } catch (e: any) { setError(e.message || 'Upload failed'); }
    finally { setUploading(false); }
  };

  const handleFaceCapture = async (base64: string) => {
    setShowCamera(false);
    setSelfieBase64(base64);
    const docBase64 = uploads['id_front']?.base64;
    if (!demoMode) {
      try {
        const result = await apiClient.verifyFace(base64, docBase64);
        setFaceVerifyResult(result);
      } catch (e) { console.warn('Face verify:', e); }
    } else {
      setFaceVerifyResult({ is_live_person: true, good_quality: true, face_match: true, confidence: 92, notes: 'Demo mode verification' });
    }
  };

  const next = async () => { setError(null); await saveDraft(); setStep(s => Math.min(s + 1, STEPS.length - 1)); };
  const back = () => setStep(s => Math.max(s - 1, 0));

  const submit = async () => {
    setSubmitting(true); setError(null); setOutstanding(null);
    // Every *-marked field must be filled: pop up exactly what is
    // outstanding (with jump-to-step) instead of failing server-side.
    const missing = validateAll();
    if (missing.length > 0) {
      setSubmitting(false);
      setOutstanding(missing);
      return;
    }
    const payload = {
      ...form,
      fullName: `${form.personal.legal_first_name} ${form.personal.legal_last_name}`,
      dob: form.personal.date_of_birth,
      nationality: form.personal.nationality,
      documentType: form.identity.document_type,
      documentNumber: form.identity.document_number,
      incomeRange: form.financial.annual_income_range || '< R50k',
      netWorthRange: form.financial.net_worth_range || '< R50k',
      tradingExperience: form.trading.years_trading_experience || 'None',
      selfieBase64: selfieBase64 || undefined,
      documents: Object.entries(uploads).map(([type, d]) => ({ type, url: d.url || '#', filename: d.filename })),
    };
    if (demoMode) {
      localStorage.setItem('xm_kyc_status', 'submitted');
      const q = JSON.parse(localStorage.getItem('kyc_applications_queue') || '[]');
      const demoId = `KYC-DEMO-${Date.now()}`;
      q.push({ id: demoId, ...payload, status: 'pending', submittedAt: new Date().toLocaleString() });
      localStorage.setItem('kyc_applications_queue', JSON.stringify(q));
      try {
        localStorage.setItem('xm_kyc_ref', demoId);
        localStorage.setItem('xm_kyc_submitted_at', new Date().toISOString());
      } catch (_) {}
      setTimeout(() => { setSubmitting(false); onSuccess ? onSuccess() : navigate('/dashboard'); }, 1200);
      return;
    }
    try {
      const res: any = await apiClient.submitKyc(payload);
      localStorage.setItem('xm_kyc_status', 'submitted');
      try {
        const appId = res?.application?.id || res?.id;
        if (appId) localStorage.setItem('xm_kyc_ref', String(appId));
        localStorage.setItem('xm_kyc_submitted_at', new Date().toISOString());
        if (res?.emailed === false) {
          console.warn('KYC emailed copy failed:', res?.email_error || 'unknown');
        }
      } catch (_) { /* storage best-effort */ }
      onSuccess ? onSuccess() : navigate('/dashboard');
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Submission failed');
    } finally { setSubmitting(false); }
  };

  // ── Step renderers ──────────────────────────────────────────────────────────
  const steps: Record<number, React.ReactNode> = {
    // Step 0 — Legal & Identity
    0: (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
        {[
          ['Legal first name', 'personal', 'legal_first_name', true],
          ['Legal middle name', 'personal', 'legal_middle_name', false],
          ['Legal last name', 'personal', 'legal_last_name', true],
        ].map(([label, sec, field, req]) => (
          <Field key={field as string} label={label as string} required={!!req}>
            <input className={ic()} value={(form as any)[sec as string][field as string]} onChange={e => patch(sec as string, field as string, e.target.value)} />
          </Field>
        ))}
        <Field label="Date of birth" required><input type="date" className={ic()} value={form.personal.date_of_birth} onChange={e => patch('personal','date_of_birth',e.target.value)} style={{colorScheme:'dark'}} /></Field>
        <Field label="Gender"><select className={sc()} value={form.personal.gender} onChange={e => patch('personal','gender',e.target.value)}><option value="">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option></select></Field>
        <Field label="Nationality" required><input className={ic()} value={form.personal.nationality} onChange={e => patch('personal','nationality',e.target.value)} placeholder="e.g. South African"/></Field>
        <Field label="Country of residence" required>
          <select className={sc()} value={form.personal.country_of_residence} onChange={e => patch('personal','country_of_residence',e.target.value)}>
            <option value="">Select country</option>
            {COUNTRIES.filter(c => c.code !== 'OTHER').map(c => <option key={c.code} value={c.name}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Place of birth"><input className={ic()} value={form.personal.place_of_birth} onChange={e => patch('personal','place_of_birth',e.target.value)}/></Field>
        <Field label="Document type" required><select className={sc()} value={form.identity.document_type} onChange={e => patch('identity','document_type',e.target.value)}>{DOC_TYPES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}</select></Field>
        <Field label="Document number" required><input className={ic()} value={form.identity.document_number} onChange={e => patch('identity','document_number',e.target.value)}/></Field>
        <Field label="Issuing country" required>
          <select className={sc()} value={form.identity.issuing_country} onChange={e => patch('identity','issuing_country',e.target.value)}>
            <option value="">Select country</option>
            {COUNTRIES.filter(c => c.code !== 'OTHER').map(c => <option key={c.code} value={c.name}>{c.name}</option>)}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Issue date"><input type="date" className={ic()} value={form.identity.issue_date} onChange={e => patch('identity','issue_date',e.target.value)} style={{colorScheme:'dark'}}/></Field>
          <Field label="Expiry date"><input type="date" className={ic()} value={form.identity.expiry_date} onChange={e => patch('identity','expiry_date',e.target.value)} style={{colorScheme:'dark'}}/></Field>
        </div>
      </div>
    ),

    // Step 1 — Address (Google Maps)
    1: (
      <div className="space-y-5 mt-4">
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-400 bg-zinc-900/40 p-3 rounded-lg border border-zinc-800">
          <MapPin className="w-4 h-4 text-rose-400 flex-shrink-0"/>
          Start typing your address — Google Maps will auto-complete and verify it.
        </div>
        <div className="grid grid-cols-1 gap-5">
          <Field label="Street address line 1" required>
            <div className="relative">
              <input
                ref={addressInputRef}
                className={ic()}
                value={form.address.street_line_1}
                onChange={e => { patch('address','street_line_1',e.target.value); setAddressVerified(false); }}
                placeholder="Start typing your address..."
              />
              {addressVerified && (
                <span className="absolute right-3 top-3 flex items-center gap-1 text-emerald-400 text-[10px] font-mono">
                  <CheckCircle className="w-3.5 h-3.5"/> Verified
                </span>
              )}
            </div>
          </Field>
          <Field label="Apt / Suite / Block">
            <input className={ic()} value={form.address.street_line_2} onChange={e => patch('address','street_line_2',e.target.value)}/>
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="City" required><input className={ic()} value={form.address.city} onChange={e => patch('address','city',e.target.value)}/></Field>
            <Field label="Province / State"><input className={ic()} value={form.address.province_state} onChange={e => patch('address','province_state',e.target.value)}/></Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Postal code"><input className={ic()} value={form.address.postal_code} onChange={e => patch('address','postal_code',e.target.value)}/></Field>
            <Field label="Country" required>
              <select className={sc()} value={form.address.country} onChange={e => patch('address','country',e.target.value)}>
                <option value="">Select country</option>
                {COUNTRIES.filter(c => c.code !== 'OTHER').map(c => <option key={c.code} value={c.name}>{c.name}</option>)}
              </select>
            </Field>
          </div>
        </div>
        {!addressVerified && form.address.street_line_1 && (
          <p className="text-amber-400 text-[10px] font-mono flex items-center gap-1">
            <AlertCircle className="w-3 h-3"/> Address not yet verified via Google Maps — please select from the autocomplete dropdown.
          </p>
        )}
      </div>
    ),

    // Step 2 — Financial & Trading
    2: (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
        <Field label="Employment status" required>
          <select className={sc()} value={form.financial.employment_status} onChange={e => patch('financial','employment_status',e.target.value)}>
            <option value="">Select</option>
            {['Employed','Self-employed','Unemployed','Retired','Student'].map(v => <option key={v} value={v.toLowerCase().replace('-','_')}>{v}</option>)}
          </select>
        </Field>
        <Field label="Employer / Company name"><input className={ic()} value={form.financial.employer_name} onChange={e => patch('financial','employer_name',e.target.value)}/></Field>
        <Field label="Occupation"><input className={ic()} value={form.financial.occupation} onChange={e => patch('financial','occupation',e.target.value)}/></Field>
        <Field label="Source of funds" required>
          <select className={sc()} value={form.financial.source_of_funds} onChange={e => patch('financial','source_of_funds',e.target.value)}>
            <option value="">Select origin</option>
            {['Salary','Business profits','Investments','Inheritance','Savings'].map(v => <option key={v}>{v}</option>)}
          </select>
        </Field>
        <Field label="Annual income range">
          <select className={sc()} value={form.financial.annual_income_range} onChange={e => patch('financial','annual_income_range',e.target.value)}>
            <option value="">Select</option>{INCOME_RANGES.map(r => <option key={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Net worth range">
          <select className={sc()} value={form.financial.net_worth_range} onChange={e => patch('financial','net_worth_range',e.target.value)}>
            <option value="">Select</option>{INCOME_RANGES.map(r => <option key={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Trading experience" required>
          <select className={sc()} value={form.trading.years_trading_experience} onChange={e => patch('trading','years_trading_experience',e.target.value)}>
            <option value="">Select</option>{EXPERIENCE.map(r => <option key={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Knowledge level" required>
          <select className={sc()} value={form.trading.trading_knowledge_level} onChange={e => patch('trading','trading_knowledge_level',e.target.value)}>
            <option value="">Select</option>{['Beginner','Intermediate','Advanced','Professional'].map(v => <option key={v}>{v}</option>)}
          </select>
        </Field>
        <div className="md:col-span-2">
          <Field label="Risk appetite" required>
            <select className={sc()} value={form.trading.risk_appetite} onChange={e => patch('trading','risk_appetite',e.target.value)}>
              <option value="">Select</option>{RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
            </select>
          </Field>
        </div>
        <div className="md:col-span-2 p-3 bg-zinc-950 rounded border border-zinc-800 flex items-start gap-3">
          <input type="checkbox" id="isPEP" className="mt-1 accent-rose-500" checked={form.financial.is_politically_exposed} onChange={e => patch('financial','is_politically_exposed',e.target.checked)}/>
          <label htmlFor="isPEP" className="text-xs font-mono text-zinc-300"><strong>PEP Declaration:</strong> I am or have been associated with a Politically Exposed Person.</label>
        </div>
        {form.financial.is_politically_exposed && (
          <div className="md:col-span-2">
            <Field label="Describe PEP duties / associations" required>
              <textarea className={ic()} rows={3} value={form.financial.pep_details} onChange={e => patch('financial','pep_details',e.target.value)} placeholder="Official role, timeline, jurisdiction..."/>
            </Field>
          </div>
        )}
      </div>
    ),
  };

  // Step 3 — Tax & Compliance (country-aware)
  const taxStep = (
    <div className="space-y-6 mt-4">
      {/* Multi-country tax residency dropdown */}
      <Field label="Tax residency country / countries" required>
        <select
          className={sc()}
          value=""
          onChange={e => {
            const val = e.target.value;
            if (val && !form.tax.tax_residency_countries.includes(val)) {
              patch('tax','tax_residency_countries',[...form.tax.tax_residency_countries, val]);
            }
          }}
        >
          <option value="">Add a country...</option>
          {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
        {/* Selected countries chips */}
        {form.tax.tax_residency_countries.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {form.tax.tax_residency_countries.map(code => {
              const c = COUNTRIES.find(x => x.code === code);
              return (
                <span key={code} className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-950/40 border border-rose-800/40 rounded-full text-[11px] font-mono text-rose-300">
                  {c?.name || code}
                  <button type="button" onClick={() => patch('tax','tax_residency_countries',form.tax.tax_residency_countries.filter(x => x !== code))} className="text-rose-500 hover:text-white">×</button>
                </span>
              );
            })}
          </div>
        )}
      </Field>

      {/* Per-country TIN fields */}
      {selectedTaxCountries.map(c => (
        <div key={c.code} className="p-4 bg-zinc-900/40 rounded-xl border border-zinc-800">
          <p className="text-rose-400 font-mono text-[10px] uppercase tracking-widest mb-3 font-bold">{c.name} — Tax Details</p>
          <Field label={c.tinLabel} required={!form.tax.has_no_tax_number}>
            <input
              className={ic()}
              value={form.tax.has_no_tax_number ? '' : form.tax.tax_identification_number}
              disabled={form.tax.has_no_tax_number}
              onChange={e => patch('tax','tax_identification_number',e.target.value)}
              placeholder={form.tax.has_no_tax_number ? 'No tax number declared' : c.tinFormat}
            />
          </Field>
          <label className="mt-2 flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="accent-rose-500"
              checked={!!form.tax.has_no_tax_number}
              onChange={e => {
                patch('tax','has_no_tax_number',e.target.checked);
                if (e.target.checked) patch('tax','tax_identification_number','');
              }}
            />
            <span className="text-[11px] font-mono text-zinc-400">I do not have a tax number</span>
          </label>
          {c.fatcaRelevant && (
            <div className="mt-3 p-3 bg-amber-950/20 border border-amber-800/30 rounded-lg text-xs font-mono text-amber-300 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5"/>
              <span><strong>FATCA Notice:</strong> As a {c.name} tax resident, you are subject to FATCA reporting requirements. Please complete the declarations below.</span>
            </div>
          )}
        </div>
      ))}

      {/* Compliance attestations */}
      <div className="space-y-3 bg-zinc-900/60 p-4 rounded-xl border border-zinc-800">
        <h3 className="text-rose-400 font-mono text-xs uppercase tracking-widest font-semibold flex items-center gap-2">
          <ShieldCheck className="w-4 h-4"/> Compliance Attestation — Sovereign Trust Framework
        </h3>
        {[
          { section:'tax', field:'us_person_fatca', text:'I am a US person (citizen, resident, green card) for FATCA compliance', show: true },
          { section:'tax', field:'fatca_declaration_acknowledged', text:'I acknowledge the FATCA / CRS reporting policies', show: true },
          { section:'declarations', field:'terms_accepted', text:'I accept the general SANS Mercantile Terms of Execution', show: true },
          { section:'declarations', field:'privacy_accepted', text:'I consent to the processing of identity profiles in alignment with localized privacy rules', show: true },
          { section:'declarations', field:'aml_consent', text:'I voluntarily submit to AML/CTF automated screenings', show: true },
          { section:'declarations', field:'sanctions_screening_consent', text:'I consent to regular global sanctions database verification', show: true },
        ].filter(d => d.show).map(({ section, field, text }) => (
          <label key={field} className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-0.5 accent-rose-500" checked={(form as any)[section][field]} onChange={e => patch(section, field, e.target.checked)}/>
            <span className="text-xs font-mono text-zinc-300 group-hover:text-white transition">{text}</span>
          </label>
        ))}
      </div>
    </div>
  );

  // Step 4 — Documents + Face Verification
  const docStep = (
    <div className="space-y-5 mt-4">
      <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-xl p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0"/>
        <div>
          <p className="text-xs font-mono font-bold text-white uppercase tracking-wider">AI-Assisted Document Verification</p>
          <p className="text-[10px] text-zinc-400 mt-0.5 leading-relaxed">Uploaded documents are analysed by our Gemini AI engine to verify authenticity, cross-reference personal details, and flag anomalies in real time.</p>
        </div>
      </div>

      {/* Document uploads */}
      {[
        { key:'id_front', label:'Government ID / Passport (Front) *', desc:'Must show photo, name, ID number, DOB and expiry clearly.' },
        { key:'id_back',  label:`National ID Card (Back${['national_id','drivers_license','residence_permit'].includes(form.identity.document_type) ? ' — required' : ' — if applicable'})`, desc:'Barcode, machine-readable zone, or signature strip.' },
        { key:'proof_of_address', label:'Proof of Residence (< 3 months) *', desc:'Utility bill or bank statement. Name + address must match form.' },
      ].map(({ key, label, desc }) => (
        <div key={key} className="border border-zinc-800 bg-zinc-950/60 rounded-xl p-4 hover:bg-zinc-950 transition">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <p className="font-mono text-xs font-bold text-white uppercase">{label}</p>
              <p className="text-[10px] text-zinc-400 mt-0.5">{desc}</p>
            </div>
            <label htmlFor={`file-${key}`} className="shrink-0 px-3 py-1.5 bg-zinc-900 border border-zinc-700 hover:border-zinc-600 rounded text-[11px] font-mono text-zinc-300 flex items-center gap-1.5 cursor-pointer transition">
              <UploadCloud className="w-3.5 h-3.5"/>
              <input id={`file-${key}`} type="file" className="hidden" accept="image/jpeg,image/png,application/pdf" onChange={e => handleUpload(e.target.files?.[0] || null, key)}/>
              Upload
            </label>
          </div>
          {uploads[key] && (
            <div className="mt-2 p-2 bg-zinc-900/50 rounded border border-rose-500/20 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/>
              <p className="text-[11px] font-mono text-zinc-300 truncate">{uploads[key].filename}</p>
              {verifyingDoc === key && <Loader2 className="w-3.5 h-3.5 text-rose-400 animate-spin ml-auto"/>}
            </div>
          )}
          <VerifyBadge result={docVerifyResults[key]}/>
        </div>
      ))}

      {/* Face / Liveness Verification */}
      <div className="border border-zinc-800 bg-zinc-950/60 rounded-xl p-4 hover:bg-zinc-950 transition">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            <p className="font-mono text-xs font-bold text-white uppercase">Biometric Face Verification</p>
            <p className="text-[10px] text-zinc-400 mt-0.5">Live camera capture — AI will compare your selfie with your uploaded ID/passport.</p>
          </div>
          <button
            onClick={() => setShowCamera(true)}
            className="shrink-0 px-3 py-1.5 bg-rose-950/40 border border-rose-800/40 hover:border-rose-500 rounded text-[11px] font-mono text-rose-300 flex items-center gap-1.5 transition"
          >
            <Camera className="w-3.5 h-3.5"/> Open Camera
          </button>
        </div>
        {selfieBase64 && (
          <div className="mt-3 flex items-start gap-3">
            <img src={`data:image/jpeg;base64,${selfieBase64}`} alt="Selfie" className="w-16 h-16 rounded-lg object-cover border border-zinc-700"/>
            <div>
              <p className="text-[11px] font-mono text-emerald-400 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5"/> Selfie captured</p>
              <VerifyBadge result={faceVerifyResult}/>
            </div>
          </div>
        )}
      </div>
      {uploading && <p className="text-xs font-mono text-rose-400 animate-pulse">Syncing document...</p>}
    </div>
  );

  // Step 5 — Review & Submit
  const reviewStep = (
    <div className="space-y-5 mt-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Field label="Verification email"><input className={`${ic()} opacity-60 cursor-not-allowed`} readOnly value={form.contact.email}/></Field>
        <Field label="Phone" required>
          <div className="flex gap-2">
            <input className={`${ic()} w-20`} value={form.contact.phone_country_code} onChange={e => patch('contact','phone_country_code',e.target.value)}/>
            <input className={ic()} value={form.contact.phone_number} onChange={e => patch('contact','phone_number',e.target.value)} placeholder="082 123 4567"/>
          </div>
        </Field>
      </div>

      {/* Solemn declaration */}
      <div className="p-3 bg-zinc-950 rounded border border-zinc-800 flex items-start gap-3">
        <input type="checkbox" id="solemnDecl" className="mt-1 accent-rose-500" checked={form.declarations.accurate_information_declaration} onChange={e => patch('declarations','accurate_information_declaration',e.target.checked)}/>
        <label htmlFor="solemnDecl" className="text-[11px] font-mono text-zinc-300 leading-relaxed">
          <strong>I declare under penalty of perjury that all details and uploaded files correspond strictly to my legal, true, and active personal assets, accounts, and residential status.</strong>
        </label>
      </div>

      {/* Preview dossier */}
      <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 text-xs font-mono space-y-2">
        <p className="text-rose-400 uppercase font-bold text-[10px] tracking-widest border-b border-zinc-800 pb-1.5">PREVIEW AML DOSSIER</p>
        <p className="text-zinc-400"><strong>Name:</strong> <span className="text-white">{form.personal.legal_first_name} {form.personal.legal_last_name || '—'}</span></p>
        <p className="text-zinc-400"><strong>Identity:</strong> <span className="text-white uppercase">{form.identity.document_type}</span> · {form.identity.document_number || '—'}</p>
        <p className="text-zinc-400"><strong>Address:</strong> <span className="text-white">{form.address.street_line_1}{form.address.city ? `, ${form.address.city}` : ''}{form.address.country ? ` (${form.address.country})` : ''}{addressVerified ? ' ✓' : ''}</span></p>
        <p className="text-zinc-400"><strong>Tax countries:</strong> <span className="text-white">{selectedTaxCountries.map(c => c.name).join(', ') || '—'}</span></p>
        <p className="text-zinc-400"><strong>Risk profile:</strong> <span className="text-rose-400 font-bold uppercase">{form.trading.risk_appetite || '—'}</span></p>
        <p className="text-zinc-400"><strong>Docs uploaded:</strong> <span className="text-white">{Object.keys(uploads).length}</span>
          {selfieBase64 ? <span className="text-emerald-400 ml-2">· Biometric captured</span> : <span className="text-amber-400 ml-2">· No selfie</span>}
        </p>
      </div>
    </div>
  );

  const stepContent: Record<number, React.ReactNode> = {
    ...steps, 3: taxStep, 4: docStep, 5: reviewStep,
  };

  return (
    <>
      {showCamera && <FaceCameraModal onCapture={handleFaceCapture} onClose={() => setShowCamera(false)}/>}
      <div className="p-1 min-h-[500px] flex items-center justify-center font-sans">
        <div className="bg-zinc-950/30 border border-zinc-800/40 rounded-xl shadow-2xl w-full p-4 sm:p-6 backdrop-blur-md">

          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-900 pb-4 mb-5 gap-3">
            <div>
              <h2 className="text-lg font-serif italic text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-rose-500"/> SANS AML Compliance Dossier
              </h2>
              <p className="text-[10px] text-zinc-400 font-mono mt-1">
                {demoMode ? 'PROVISIONAL SANDBOX SESSION' : `Ledger completion: ${completion}%`}
                {saving && <span className="ml-2 text-rose-400">· Saving...</span>}
              </p>
            </div>
            <span className="px-2 py-1 bg-rose-950/40 text-rose-400 font-bold border border-rose-900/50 rounded-md font-mono text-[9px]">
              STAGE {step + 1} / {STEPS.length}
            </span>
          </div>

          {/* Step rail */}
          <div className="flex gap-1 mb-6 overflow-x-auto py-1">
            {STEPS.map((name, i) => (
              <button key={name} type="button" onClick={() => setStep(i)}
                className={`px-2.5 py-1 text-[9px] font-mono rounded-md whitespace-nowrap border transition ${i === step ? 'bg-rose-950/40 text-rose-400 border-rose-500/30 font-bold' : 'bg-zinc-900/20 text-zinc-500 border-zinc-800/40 hover:text-zinc-200'}`}>
                {i + 1}. {name}
              </button>
            ))}
          </div>

          {error && (
            <div className="text-rose-400 text-xs font-mono mb-5 p-3 bg-rose-950/20 rounded border border-rose-500/30 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5"/><span>{error}</span>
            </div>
          )}

          {/* Outstanding-items popup: every *-marked field still empty */}
          {outstanding && (
            <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 p-4">
              <div className="w-full max-w-md bg-zinc-950 border border-rose-500/30 rounded-2xl p-6 space-y-4">
                <div>
                  <h2 className="text-base font-bold text-white font-mono">
                    {outstanding.length} required item{outstanding.length === 1 ? "" : "s"} outstanding
                  </h2>
                  <p className="text-[11px] text-zinc-400 font-mono mt-1">
                    Fill the starred (*) fields below, then dispatch again.
                  </p>
                </div>
                <ul className="space-y-1.5 max-h-64 overflow-y-auto">
                  {outstanding.map((m, i) => (
                    <li key={i}>
                      <button
                        type="button"
                        onClick={() => { setOutstanding(null); setStep(m.step); }}
                        className="w-full text-left px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/40 hover:border-rose-500/50 text-xs font-mono text-zinc-200 transition"
                      >
                        <span className="text-rose-400 font-bold">•</span> {m.label}
                        <span className="text-zinc-500"> — step {m.step + 1}</span>
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => setOutstanding(null)}
                  className="w-full py-2 border border-zinc-700 rounded-lg text-xs font-mono text-zinc-300 hover:text-white transition"
                >
                  Back to the form
                </button>
              </div>
            </div>
          )}

          <div className="min-h-[300px] border border-zinc-800/60 bg-zinc-900/10 p-5 rounded-xl">
            {stepContent[step]}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center mt-7 gap-3">
            <button type="button" onClick={back} disabled={step === 0}
              className="px-4 py-2 border border-zinc-800 bg-zinc-950 text-zinc-300 font-mono text-[11px] rounded-lg disabled:opacity-30 hover:bg-zinc-900 transition flex items-center gap-1.5">
              <ArrowLeft className="w-3.5 h-3.5"/> Prev
            </button>
            <div className="flex gap-2">
              <button type="button" onClick={saveDraft} disabled={saving}
                className="px-3 py-2 border border-zinc-800 bg-zinc-950 text-zinc-400 font-mono text-[11px] rounded-lg hover:bg-zinc-900 transition flex items-center gap-1">
                <Save className="w-3.5 h-3.5"/> Save
              </button>
              {step < STEPS.length - 1 ? (
                <button type="button" onClick={next}
                  className="px-4 py-2 bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 rounded-lg font-bold font-mono text-[11px] text-white transition flex items-center gap-1.5">
                  Continue <ArrowRight className="w-3.5 h-3.5"/>
                </button>
              ) : (
                <button type="button" onClick={submit} disabled={submitting || !form.declarations.accurate_information_declaration}
                  className="px-5 py-2 bg-rose-600 hover:bg-rose-500 text-white border border-rose-500/20 font-bold font-mono text-[11px] rounded-lg disabled:opacity-30 transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(225,29,72,0.25)]">
                  {submitting ? <><Loader2 className="w-4 h-4 animate-spin"/> Transmitting...</> : 'Dispatch AML Dossier'}
                </button>
              )}
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
