import React, { useEffect, useState } from "react";
import { CreditCard, CheckCircle2, Loader2, AlertTriangle } from "lucide-react";
import apiClient from "../api/apiClient";

interface Plan {
  plan_id: string;
  name: string;
  description?: string;
  price: number;
  currency: string;
  features: string[];
}

interface SubscriptionInfo {
  subscription_id: string;
  plan_id: string;
  status: string;
  payment_provider: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
}

export default function Billing({ demoMode }: { demoMode?: boolean }) {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [redirecting, setRedirecting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [plansRes, subRes] = await Promise.allSettled([
          apiClient.getPlans(),
          apiClient.getMySubscription(),
        ]);
        if (cancelled) return;
        if (plansRes.status === "fulfilled") {
          // Backend returns the plans array directly (or {plans:[...]}).
          // Either can be null (empty body) -- never read .data blind.
          const v: any = plansRes.value;
          const body = v?.data ?? v;
          setPlans(body?.plans ?? (Array.isArray(body) ? body : []));
        }
        if (subRes.status === "fulfilled") {
          // 200 + null body = signed in but no subscription yet.
          const v: any = subRes.value;
          const body = v?.data ?? v;
          setSubscription(
            body?.subscription ?? (body && typeof body === "object" ? body : null)
          );
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load billing information.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const myPlanId = subscription?.plan_id || null;
  const myPlan = plans.find((p) => p.plan_id === myPlanId) || null;
  const holdingActive = subscription?.status === "active";
  const holdingPaid = holdingActive && myPlan !== null && Number(myPlan.price) > 0;
  const [cancelling, setCancelling] = useState(false);

  const goLive = () => {
    try {
      localStorage.setItem("demoMode", "false");
    } catch (_) {}
    window.location.reload();
  };

  const subscribeWithPayFast = async (plan: Plan) => {
    setError(null);
    // Subscribing is a live-mode action; demo mode keeps everything
    // read-only. Offer the switch inline instead of a dead button.
    if (demoMode) {
      setError("Subscriptions need live mode — your demo stays intact. Switch below to continue.");
      return;
    }
    // Free tier needs no checkout: grant it directly.
    if (!plan.price || Number(plan.price) <= 0) {
      setRedirecting(plan.plan_id);
      try {
        await apiClient.post("/api/v1/payment/subscriptions/ensure-free", {});
        const sub: any = await apiClient.getMySubscription();
        const body = sub?.data ?? sub;
        setSubscription(body?.subscription ?? (body && typeof body === "object" ? body : null));
      } catch (e: any) {
        setError(e?.message || "Could not activate the free plan.");
      } finally {
        setRedirecting(null);
      }
      return;
    }
    setRedirecting(plan.plan_id);
    try {
      const origin = window.location.origin;
      const result = await apiClient.createPayfastSubscription({
        plan_id: plan.plan_id,
        return_url: `${origin}/dashboard/billing?status=success`,
        cancel_url: `${origin}/dashboard/billing?status=cancelled`,
        notify_url: "https://api.priv.sansmercantile.com/api/payfast/itn",
        billing_frequency: "3",
      });
      const url = result.data?.subscription_url;
      if (!url) throw new Error("PayFast did not return a checkout URL.");
      // Hand the browser off to PayFast's hosted checkout. The backend
      // has already generated and signed the payload server-side; the
      // frontend never sees or needs the merchant passphrase.
      window.location.href = url;
    } catch (e: any) {
      setRedirecting(null);
      const detail: string = e?.message || "Could not start PayFast checkout. Please try again.";
      // Backend refuses duplicates/downgrades with 400 "already has an
      // active subscription" -- translate to actionable copy instead of
      // the raw row text.
      setError(
        /already has an active subscription/i.test(detail)
          ? `You already hold an active plan${myPlan ? ` (${myPlan.name})` : ""}. Cancel it below first, then subscribe to a different one.`
          : detail
      );
    }
  };

  const cancelSubscription = async () => {
    if (!subscription?.subscription_id) return;
    if (!window.confirm(`Cancel your ${myPlan?.name || subscription.plan_id} subscription? It stays active until the period ends.`)) return;
    setCancelling(true);
    setError(null);
    try {
      await apiClient.cancelPayfastSubscription(subscription.subscription_id);
      const sub: any = await apiClient.getMySubscription();
      const body = sub?.data ?? sub;
      setSubscription(body?.subscription ?? (body && typeof body === "object" ? body : null));
    } catch (e: any) {
      setError(e?.message || "Could not cancel the subscription.");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-white/60 p-6">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading billing…
      </div>
    );
  }

  return (
    <div className="p-2 sm:p-4 space-y-6">
      <div className="flex items-center gap-2">
        <CreditCard className="w-5 h-5 text-emerald-400" />
        <h1 className="text-xl font-semibold text-white">Billing & Subscription</h1>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-300 text-sm rounded-lg p-3">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="flex-1">{error}</span>
          {demoMode && (
            <button
              onClick={goLive}
              className="shrink-0 px-3 py-1 rounded-lg bg-white text-black font-mono text-xs font-bold"
            >
              Go live
            </button>
          )}
        </div>
      )}

      {subscription && subscription.status === "active" && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <div className="text-sm text-white/90 flex-1">
            Active plan: <span className="font-semibold">{myPlan?.name || subscription.plan_id}</span> via{" "}
            {subscription.payment_provider}
            {subscription.current_period_end && (
              <> — renews {new Date(subscription.current_period_end).toLocaleDateString()}</>
            )}
          </div>
          {holdingPaid && (
            <button
              onClick={cancelSubscription}
              disabled={cancelling}
              className="shrink-0 px-3 py-1.5 rounded-lg border border-red-500/40 text-red-300 font-mono text-xs hover:bg-red-500/10 transition disabled:opacity-50"
            >
              {cancelling ? "Cancelling…" : "Cancel plan"}
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans.map((plan) => (
          <div
            key={plan.plan_id}
            className="bg-white/5 border border-white/10 rounded-xl p-5 flex flex-col gap-3"
          >
            <div>
              <h3 className="text-white font-semibold">{plan.name}</h3>
              {plan.description && <p className="text-white/50 text-sm mt-1">{plan.description}</p>}
            </div>
            <div className="text-2xl font-bold text-white">
              {plan.currency} {plan.price}
              <span className="text-sm font-normal text-white/40">/mo</span>
            </div>
            {Array.isArray(plan.features) && plan.features.length > 0 && (
              <ul className="text-sm text-white/60 space-y-1 flex-1">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400/70 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
            )}
            <button
              onClick={() => subscribeWithPayFast(plan)}
              disabled={!!redirecting || myPlanId === plan.plan_id || (holdingPaid && Number(plan.price) > 0)}
              className="mt-2 w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-medium py-2 text-sm flex items-center justify-center gap-2 transition-colors"
              title={
                myPlanId === plan.plan_id
                  ? "Your current subscription"
                  : holdingPaid && Number(plan.price) > 0
                    ? `You hold ${myPlan?.name || "a plan"} — cancel it first to switch`
                    : demoMode
                      ? "Works in live mode"
                      : undefined
              }
            >
              {redirecting === plan.plan_id ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Redirecting to checkout…
                </>
              ) : myPlanId === plan.plan_id ? (
                "Current Subscription"
              ) : (
                "Subscribe"
              )}
            </button>
          </div>
        ))}
      </div>

      {plans.length === 0 && !error && (
        <div className="text-white/50 text-sm">No plans are currently available.</div>
      )}

      <p className="text-xs text-white/30">
        You'll be redirected to a secure checkout to complete payment, then returned here.
        Prices are shown in USD; your card will be charged in your local currency at checkout.
      </p>
    </div>
  );
}
