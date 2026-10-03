import LegalPage, { H2, P, Section } from "./LegalPage";

export default function Terms() {
  return (
    <LegalPage title="PRIV CORE - TERMS AND CONDITIONS (PLACEHOLDER)">
      <Section>
        <P>
          DESIGN NOTE: The final design, wording and presentation of these terms will be provided
          by the product owner before public release. This placeholder exists so that installation
          is gated behind an explicit acceptance step from day one.
        </P>
      </Section>

      <Section>
        <H2>1. SERVICE.</H2>
        <P>
          Priv Core ("the Service") connects your installed MetaTrader 5 terminal to your Priv
          account so that orders placed in Priv are executed in that terminal while the Service is
          running.
        </P>
      </Section>

      <Section>
        <H2>2. CONNECTIVITY.</H2>
        <P>
          The Service runs in the background of your computer and requires an active internet
          connection. It starts when you sign in to Windows and reconnects automatically; keep
          internet access enabled for it.
        </P>
      </Section>

      <Section>
        <H2>3. BROKER RULE.</H2>
        <P>
          Automated trading is available only for Deriv MetaTrader 5 accounts. If your terminal is
          logged into a non-Deriv server, automated trading is blocked regardless of your
          subscription tier. In that case contact an administrator.
        </P>
      </Section>

      <Section>
        <H2>4. ACCOUNT ORDER.</H2>
        <P>
          After installation, sign in to Priv first, then sign in to your Deriv account in
          MetaTrader 5.
        </P>
      </Section>

      <Section>
        <H2>5. DATA.</H2>
        <P>
          Your MT5 login number, server name, account metrics (balance, equity, leverage, trade
          permission) and trade events are sent to Priv. Your MT5 password never leaves your
          machine.
        </P>
      </Section>

      <Section>
        <H2>6. RISK.</H2>
        <P>
          Trading financial instruments involves substantial risk of loss. Automated execution
          is not investment advice and does not guarantee results. You remain responsible for
          every order placed through your accounts.
        </P>
      </Section>

      <Section>
        <H2>7. AVAILABILITY.</H2>
        <P>
          The Service may be interrupted for maintenance or due to events beyond our control.
          Maximum liability is limited to the fees you paid for the applicable tier in the
          preceding twelve months, to the extent permitted by law.
        </P>
      </Section>

      <Section>
        <H2>8. CHANGES.</H2>
        <P>Continued use after updated terms are posted constitutes acceptance of them.</P>
      </Section>

      <Section>
        <P>
          By continuing this installation you acknowledge that you have read and accept these
          terms and the accompanying End User License Agreement.
        </P>
      </Section>
    </LegalPage>
  );
}
