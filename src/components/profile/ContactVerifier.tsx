import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import apiClient from '../../api/apiClient';

export interface VerifiedEntry {
  channel: string;
  contact: string;
}

// Same normalization as the backend (_normalize_contact): email lowercased,
// phone numbers stripped of visual separators.
const norm = (kind: 'email' | 'phone', s: string) => {
  const t = (s || '').trim();
  return kind === 'email' ? t.toLowerCase() : t.replace(/[\s\-().]/g, '');
};

export const isContactVerified = (
  list: VerifiedEntry[],
  kind: 'email' | 'phone',
  contact: string
): boolean => {
  if (!contact || !contact.trim()) return false;
  const want = norm(kind, contact);
  return list.some((v) => {
    const sameKind = kind === 'email' ? v.channel === 'email' : v.channel === 'sms' || v.channel === 'whatsapp';
    return sameKind && norm(kind, v.contact) === want;
  });
};

interface Props {
  kind: 'email' | 'phone';
  contact: string;
  verified: VerifiedEntry[];
  onVerified: (list: VerifiedEntry[]) => void;
}

const errText = (e: any, fallback: string) => {
  const detail = e?.response?.data?.detail;
  return typeof detail === 'string' ? detail : detail?.message || e?.message || fallback;
};

/**
 * Verification happens here, once, in Profile. Signals only ever reads the
 * verified result (backend refuses to save a delivery contact that isn't
 * verified), so a user never has to re-enter or re-verify anything there.
 */
export default function ContactVerifier({ kind, contact, verified, onVerified }: Props) {
  const [phoneChannel, setPhoneChannel] = useState<'sms' | 'whatsapp'>('sms');
  const [code, setCode] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const ok = isContactVerified(verified, kind, contact);
  const channel = kind === 'email' ? 'email' : phoneChannel;

  if (!contact.trim()) return null;

  if (ok) {
    return (
      <div className="mt-1.5 flex items-center gap-1.5 text-[10px] font-mono text-emerald-400">
        <CheckCircle2 className="w-3 h-3" /> Verified
      </div>
    );
  }

  const send = async () => {
    setBusy(true);
    setMsg(null);
    setErr(null);
    try {
      await apiClient.requestOtp(channel, contact.trim());
      setSent(true);
      setMsg(`Code sent via ${channel} — expires in 10 minutes.`);
    } catch (e: any) {
      setErr(errText(e, 'Could not send code.'));
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!code.trim()) {
      setErr('Enter the 6-digit code.');
      return;
    }
    setBusy(true);
    setMsg(null);
    setErr(null);
    try {
      const res: any = await apiClient.confirmOtp(channel, contact.trim(), code.trim());
      const d = res?.data?.data ?? res?.data ?? {};
      onVerified(d.verified || []);
      setCode('');
      setSent(false);
    } catch (e: any) {
      setErr(errText(e, 'Verification failed.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-1.5 space-y-1.5">
      <div className="flex items-center gap-1.5 text-[10px] font-mono text-amber-400">
        <AlertTriangle className="w-3 h-3" /> Not verified — signals and reports can't be delivered here yet
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {kind === 'phone' && (
          <select
            value={phoneChannel}
            onChange={(e) => setPhoneChannel(e.target.value as 'sms' | 'whatsapp')}
            className="p-1.5 bg-zinc-950 text-white rounded border border-zinc-800 font-mono text-[10px]"
          >
            <option value="sms">SMS</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        )}
        <button
          type="button"
          onClick={send}
          disabled={busy}
          className="px-2.5 py-1.5 bg-zinc-900 border border-zinc-700 hover:border-rose-500 rounded text-[10px] font-mono text-zinc-200 disabled:opacity-50 transition"
        >
          {sent ? 'Resend code' : 'Send code'}
        </button>
        {sent && (
          <>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              placeholder="6-digit code"
              className="w-24 p-1.5 bg-zinc-950 text-white rounded border border-zinc-800 font-mono text-[10px] focus:outline-none focus:border-rose-500"
            />
            <button
              type="button"
              onClick={confirm}
              disabled={busy}
              className="px-2.5 py-1.5 bg-rose-600 hover:bg-rose-500 rounded text-[10px] font-mono text-white disabled:opacity-50 transition"
            >
              Confirm
            </button>
          </>
        )}
      </div>
      {msg && <div className="text-[10px] font-mono text-zinc-400">{msg}</div>}
      {err && <div className="text-[10px] font-mono text-rose-400">{err}</div>}
    </div>
  );
}
