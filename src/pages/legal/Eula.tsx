import LegalPage, { H2, P, Section } from "./LegalPage";

export default function Eula() {
  return (
    <LegalPage title="PRIV CORE - END USER LICENSE AGREEMENT (PLACEHOLDER)">
      <Section>
        <P>
          DESIGN NOTE: The final design, wording and presentation of this agreement will be
          provided by the product owner before public release. This placeholder exists so that
          installation is gated behind an explicit acceptance step from day one.
        </P>
      </Section>

      <Section>
        <H2>1. LICENSE GRANT.</H2>
        <P>
          Priv grants you a personal, non-exclusive, non-transferable, revocable licence to
          install and run Priv Core (the "Software") on one computer for your own trading
          activity.
        </P>
      </Section>

      <Section>
        <H2>2. WHAT THE SOFTWARE DOES.</H2>
        <P>
          The Software attaches to the MetaTrader 5 terminal installed on your computer and
          forwards trading instructions from your Priv account to that terminal over HTTPS. No
          inbound ports are opened. Your MetaTrader 5 password stays on your machine and is never
          transmitted to Priv.
        </P>
      </Section>

      <Section>
        <H2>3. INTERNET REQUIRED.</H2>
        <P>
          The Software must be able to reach Priv over the internet to function; it reconnects
          and restarts automatically with Windows.
        </P>
      </Section>

      <Section>
        <H2>4. ELIGIBLE ACCOUNTS.</H2>
        <P>
          Automated trading through the Software is supported for Deriv MetaTrader 5 accounts
          only. Accounts with other MetaTrader 5 brokers may be connected for monitoring, but
          automated trading is blocked and you must contact an administrator.
        </P>
      </Section>

      <Section>
        <H2>5. YOUR RESPONSIBILITY.</H2>
        <P>
          You are responsible for the accounts you connect, for all trading activity executed
          through them, and for keeping your Priv credentials secure.
        </P>
      </Section>

      <Section>
        <H2>6. NO WARRANTY.</H2>
        <P>
          THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
          INCLUDING FITNESS FOR A PARTICULAR PURPOSE AND MERCHANTABILITY. TRADING INVOLVES RISK
          OF LOSS.
        </P>
      </Section>

      <Section>
        <H2>7. LIMITATION OF LIABILITY.</H2>
        <P>
          TO THE MAXIMUM EXTENT PERMITTED BY LAW, PRIV SHALL NOT BE LIABLE FOR INDIRECT,
          INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING FROM USE OF THE SOFTWARE.
        </P>
      </Section>

      <Section>
        <H2>8. TERMINATION.</H2>
        <P>
          This licence terminates automatically if you breach it. Upon termination you must stop
          using and uninstall the Software.
        </P>
      </Section>

      <Section>
        <H2>9. DATA.</H2>
        <P>
          The Software transmits your MT5 login number, server name, account metrics (balance,
          equity, leverage, trade permission) and trade events. It does not transmit your MT5
          password or terminal credentials.
        </P>
      </Section>

      <Section>
        <P>
          By continuing this installation you acknowledge that you have read and accept this
          agreement and the accompanying Terms &amp; Conditions.
        </P>
      </Section>
    </LegalPage>
  );
}
