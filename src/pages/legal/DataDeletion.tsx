import LegalPage, { H2, P, UL, OL, Section } from "./LegalPage";

export default function DataDeletion() {
  return (
    <LegalPage title="Data Deletion Instructions" updated="30 September 2026">
      <Section>
        <P>
          You can request deletion of the personal data associated with your Priv account. This
          page explains how to do it, what is deleted, and what is retained and why.
        </P>
      </Section>

      <Section>
        <H2>1. How to request deletion</H2>
        <OL>
          <li>
            Email{" "}
            <a className="text-rose-400 hover:text-rose-300" href="mailto:hello@sansmercantile.com">
              hello@sansmercantile.com
            </a>{" "}
            from the address registered to your account, with the subject line{" "}
            <code className="bg-white/[0.06] border border-white/10 rounded px-1.5 py-0.5 text-[13px] text-white/85">
              Data deletion request
            </code>
            .
          </li>
          <li>
            Include the email address or username on the account so we can verify ownership. We
            may ask for a one-time verification code sent to your registered contact to confirm
            the request is yours.
          </li>
          <li>
            WhatsApp or SMS messages: reply{" "}
            <code className="bg-white/[0.06] border border-white/10 rounded px-1.5 py-0.5 text-[13px] text-white/85">
              STOP
            </code>{" "}
            at any time to opt out of future messages immediately.
          </li>
        </OL>
      </Section>

      <Section>
        <H2>2. What we delete</H2>
        <UL>
          <li>Your profile and account settings.</li>
          <li>Uploaded identity/KYC documents and their encrypted copies in storage.</li>
          <li>Notification preferences, contact verifications, and signal subscriptions.</li>
          <li>Connected broker authorisation tokens held by us.</li>
        </UL>
      </Section>

      <Section>
        <H2>3. What we retain, and why</H2>
        <UL>
          <li>
            <strong className="text-white/90">Transaction, invoice, and subscription records</strong> —
            retained for the period required by applicable financial and tax law (generally up to
            5 years), then deleted.
          </li>
          <li>
            <strong className="text-white/90">Anti-fraud and security logs</strong> — retained for
            up to 12 months for security investigations.
          </li>
          <li>
            <strong className="text-white/90">Data we must keep under a legal obligation or court order</strong>{" "}
            — retained only as long as the obligation lasts.
          </li>
        </UL>
      </Section>

      <Section>
        <H2>4. Timeline</H2>
        <P>
          We action verified deletion requests within{" "}
          <strong className="text-white/90">30 days</strong>. Some backup copies are purged on
          their normal rotation schedule within a further 35 days. You will receive a confirmation
          email when deletion is complete.
        </P>
      </Section>

      <Section>
        <H2>5. Third parties</H2>
        <P>
          If you signed in using an external identity provider (e.g. Auth0/Google), deleting data
          with us does not delete data held by that provider; manage it in that provider's account
          settings.
        </P>
      </Section>

      <Section>
        <H2>6. Contact</H2>
        <P>
          Questions:{" "}
          <a className="text-rose-400 hover:text-rose-300" href="mailto:hello@sansmercantile.com">
            hello@sansmercantile.com
          </a>
          . Sans Mercantile LTD (Pty) Ltd.
        </P>
      </Section>
    </LegalPage>
  );
}
