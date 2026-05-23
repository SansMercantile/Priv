import KycVerificationPage from './KycVerificationPage';

/** Route wrapper — full KYC flow lives in KycVerificationPage. */
export default function VerificationPage(props) {
  return <KycVerificationPage {...props} />;
}
