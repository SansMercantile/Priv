import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import { useAuth } from '../auth/useAuth';

const KycAdminReviewPage = () => {
  const { user } = useAuth();
  const [pendingKyc, setPendingKyc] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [reviewAction, setReviewAction] = useState({ status: 'pending', notes: '' });

  useEffect(() => {
    fetchPendingKyc();
  }, []);

  const fetchPendingKyc = async () => {
    try {
      const response = await apiClient.get('/admin/kyc/pending');
      setPendingKyc(response.data);
    } catch (error) {
      console.error('Error fetching pending KYC:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async () => {
    if (!selectedUser) return;
    try {
      await apiClient.post(`/admin/kyc/review`, {
        userId: selectedUser.id,
        status: reviewAction.status,
        notes: reviewAction.notes,
      });
      setReviewAction({ status: 'pending', notes: '' });
      setSelectedUser(null);
      fetchPendingKyc();
    } catch (error) {
      console.error('Error submitting KYC review:', error);
    }
  };

  if (loading) return <div className="p-8 text-white">Loading KYC Queue...</div>;

  return (
    <div className="p-8 bg-black min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-6">KYC Admin Review</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 overflow-y-auto max-h-[80vh]">
          <h2 className="text-xl font-semibold mb-4">Pending Applications</h2>
          <div className="space-y-3">
            {pendingKyc.map(app => (
              <div 
                key={app.id} 
                onClick={() => setSelectedUser(app)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${selectedUser?.id === app.id ? 'bg-blue-600' : 'bg-zinc-800 hover:bg-zinc-700'}`}
              >
                <div className="font-medium">{app.fullName || 'Unknown User'}</div>
                <div className="text-xs text-zinc-400">{app.submittedAt}</div>
              </div>
            ))}
            {pendingKyc.length === 0 && <div className="text-zinc-500 text-center py-4">No pending reviews</div>}
          </div>
        </div>

        <div className="lg:col-span-2 bg-zinc-900 p-6 rounded-xl border border-zinc-800">
          {selectedUser ? (
            <div className="space-y-6">
              <div className="flex justify-between items-center border-b border-zinc-800 pb-4">
                <h2 className="text-2xl font-bold">Review: {selectedUser.fullName}</h2>
                <span className="px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-full text-xs font-bold uppercase">Pending</span>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <section>
                  <h3 className="text-zinc-400 text-sm font-bold uppercase mb-2">Identity</h3>
                  <div className="bg-zinc-800 p-3 rounded-lg space-y-2 text-sm">
                    <p><strong>DOB:</strong> {selectedUser.dob}</p>
                    <p><strong>Nationality:</strong> {selectedUser.nationality}</p>
                    <p><strong>Doc Type:</strong> {selectedUser.documentType}</p>
                    <p><strong>Doc No:</strong> {selectedUser.documentNumber}</p>
                  </div>
                </section>
                <section>
                  <h3 className="text-zinc-400 text-sm font-bold uppercase mb-2">Financials</h3>
                  <div className="bg-zinc-800 p-3 rounded-lg space-y-2 text-sm">
                    <p><strong>Income:</strong> {selectedUser.incomeRange}</p>
                    <p><strong>Net Worth:</strong> {selectedUser.netWorthRange}</p>
                    <p><strong>Experience:</strong> {selectedUser.tradingExperience}</p>
                  </div>
                </section>
              </div>

              <div className="space-y-4">
                <h3 className="text-zinc-400 text-sm font-bold uppercase">Documents</h3>
                <div className="flex gap-4">
                  {selectedUser.documents?.map((doc, idx) => (
                    <a 
                      key={idx} 
                      href={doc.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="p-2 bg-zinc-800 border border-zinc-700 rounded text-xs hover:bg-zinc-700 transition-colors"
                    >
                      View {doc.type}
                    </a>
                  ))}
                </div>
              </div>

              <div className="mt-8 p-6 bg-zinc-800 rounded-xl border border-zinc-700 space-y-4">
                <h3 className="text-lg font-semibold">Admin Decision</h3>
                <div className="flex gap-4">
                  <select 
                    value={reviewAction.status} 
                    onChange={(e) => setReviewAction({ ...reviewAction, status: e.target.value })}
                    className="bg-black text-white p-2 rounded border border-zinc-600 flex-1"
                  >
                    <option value="pending">Keep Pending</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                    <option value="more_info">Request More Info</option>
                  </select>
                  <button 
                    onClick={handleDecision}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded font-bold transition-colors"
                  >
                    Submit Decision
                  </button>
                </div>
                <textarea 
                  placeholder="Internal notes for the decision..."
                  value={reviewAction.notes}
                  onChange={(e) => setReviewAction({ ...reviewAction, notes: e.target.value })}
                  className="w-full bg-black text-white p-3 rounded border border-zinc-600 h-24"
                />
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-zinc-500 italic">
              Select a user from the queue to begin review
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KycAdminReviewPage;
