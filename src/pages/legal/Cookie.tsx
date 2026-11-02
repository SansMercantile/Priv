import LegalPage, { H2, P, UL, Section } from "./LegalPage";

export default function Cookie() {
  return (
    <LegalPage title="Cookie Notice">
      <Section>
        <P>
          This Cookie Notice explains how Sans Mercantile uses cookies and similar technologies
          to recognize you when you visit our website, sansmercantile.com. It explains what these
          technologies are and why we use them, as well as your rights to control our use of
          them.
        </P>
      </Section>

      <Section>
        <H2>What are cookies?</H2>
        <P>
          Cookies are small data files that are placed on your computer or mobile device when you
          visit a website. Cookies are widely used by website owners in order to make their
          websites work, or to work more efficiently, as well as to provide reporting
          information.
        </P>
      </Section>

      <Section>
        <H2>Why do we use cookies?</H2>
        <P>
          We use first and third-party cookies for several reasons. Some cookies are required for
          technical reasons in order for our Websites to operate, and we refer to these as
          "essential" or "strictly necessary" cookies. Other cookies also enable us to track and
          target the interests of our users to enhance the experience on our Online Properties.
          Third parties serve cookies through our Websites for advertising, analytics and other
          purposes. This is described in more detail below.
        </P>
      </Section>

      <Section>
        <H2>Your control over cookies</H2>
        <P>
          You have the right to decide whether to accept or reject cookies. You can exercise your
          cookie preferences by clicking on the appropriate opt-out links provided in the cookie
          consent manager. The Cookie Consent Manager allows you to select which categories of
          cookies you accept or reject. Essential cookies cannot be rejected as they are strictly
          necessary to provide you with services.
        </P>
        <P>
          The means by which you can refuse cookies through your web browser controls vary from
          browser to browser, so you should visit your browser's help menu for more information.
        </P>
      </Section>

      <Section>
        <H2>Contact Us</H2>
        <UL>
          <li>Email: hello@sansmercantile.com</li>
          <li>Phone (Japan): +81 90-2356-8114</li>
          <li>Phone (South Africa): +27 66-349-6137</li>
          <li>Phone (Hong Kong): +852 5131-9039</li>
        </UL>
      </Section>
    </LegalPage>
  );
}
