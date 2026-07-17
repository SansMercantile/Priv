import React, { useState, useEffect } from "react";
import { Landmark, DollarSign, FileText, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";

interface CountryOption {
  code: string;
  name?: string;
}

const TAX_TYPES = [
  { value: "capital_gains", label: "Capital Gains" },
  { value: "income_tax", label: "Income Tax" },
  { value: "dividend_tax", label: "Dividend Tax" },
  { value: "interest_tax", label: "Interest Tax" },
  { value: "transaction_tax", label: "Transaction Tax" },
  { value: "withholding_tax", label: "Withholding Tax" },
  { value: "stamp_duty", label: "Stamp Duty" },
  { value: "vat_gst", label: "VAT / GST" },
  { value: "corporate_tax", label: "Corporate Tax" },
];

export const TaxIntelligence: React.FC = () => {
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [residency, setResidency] = useState("ZA");
  const [taxType, setTaxType] = useState("capital_gains");
  const [amount, setAmount] = useState<number>(1000);
  const [taxYear, setTaxYear] = useState<number>(new Date().getFullYear());

  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCountries = async () => {
      try {
        const res = await fetch("/api/v1/tax/supported_countries");
        const data = await res.json();
        if (data.success && Array.isArray(data.data)) {
          const opts = data.data.map((c: any) =>
            typeof c === "string" ? { code: c } : { code: c.code || c.value || c, name: c.name || c.label }
          );
          setCountries(opts);
          if (opts.length > 0) setResidency(opts[0].code);
        }
      } catch {
        setError("Could not load supported tax jurisdictions from the backend.");
      } finally {
        setLoadingCountries(false);
      }
    };
    loadCountries();
  }, []);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalculating(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/v1/tax/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tax_residency: residency,
          tax_type: taxType,
          amount,
          tax_year: taxYear,
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResult(data.data);
      } else {
        setError(data.detail || "Tax calculation failed.");
      }
    } catch (err: any) {
      setError(err.message || "Tax calculation failed.");
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Tax Intelligence</h1>
          <p className="text-white/40 text-xs mt-1 font-light font-sans">
            Estimate the tax liability on your trading activity across supported jurisdictions.
          </p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs">
          <Landmark className="w-3.5 h-3.5 text-white/50" />
          <span className="text-white/60 font-medium font-sans uppercase">
            {loadingCountries ? "Loading Jurisdictions..." : `${countries.length} Jurisdictions Supported`}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <DollarSign className="w-4 h-4 mr-2 text-white/55" />
            Calculate Liability
          </h3>
          <form onSubmit={handleCalculate} className="space-y-4">
            <div className="space-y-1">
              <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Tax Residency</label>
              <select
                value={residency}
                onChange={(e) => setResidency(e.target.value)}
                disabled={loadingCountries}
                className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
              >
                {countries.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name || c.code}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Tax Type</label>
              <select
                value={taxType}
                onChange={(e) => setTaxType(e.target.value)}
                className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
              >
                {TAX_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Amount</label>
                <input
                  type="number"
                  min={0}
                  value={amount}
                  onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Tax Year</label>
                <input
                  type="number"
                  value={taxYear}
                  onChange={(e) => setTaxYear(parseInt(e.target.value) || new Date().getFullYear())}
                  className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={calculating || loadingCountries}
              className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-3 rounded flex items-center justify-center gap-2"
            >
              {calculating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> CALCULATING...
                </>
              ) : (
                "CALCULATE"
              )}
            </button>
          </form>
        </div>

        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <FileText className="w-4 h-4 mr-2 text-white/55" />
            Result
          </h3>
          {error && (
            <div className="p-4 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}
          {!error && !result && (
            <div className="py-12 text-center font-mono text-[11px] text-zinc-600">
              Run a calculation to see the real result from Priv's tax engine.
            </div>
          )}
          {result && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono mb-2">
                <CheckCircle className="w-4 h-4" /> Calculation complete
              </div>
              <pre className="p-4 bg-neutral-950 border border-white/5 rounded text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      <p className="text-[10px] text-zinc-600 font-mono">
        Estimates only, generated by Priv's tax engine - not a substitute for professional tax advice.
      </p>
    </div>
  );
};
