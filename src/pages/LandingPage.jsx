import { useEffect } from 'react';
import { Link } from 'react-router-dom';

const previewUrl = '/dashboard/terminal?preview=broker';

const featureCards = [
  {
    title: 'Platform overview',
    desc: 'Open the full PRIV workspace and review the live intelligence dashboard.',
    href: '/dashboard',
  },
  {
    title: 'Broker terminal',
    desc: 'Jump straight into the SANS Broker Terminal preview and execute from the embedded workspace.',
    href: '/dashboard/terminal',
  },
  {
    title: 'Broker controls',
    desc: 'Review and manage connected broker accounts and broker onboarding flows.',
    href: '/dashboard/broker',
  },
];

export default function LandingPage() {
  useEffect(() => {
    document.title = 'Sans Mercantile™ | PRIV Platform Access';
  }, []);

  return (
    <div className="min-h-screen bg-black text-white neural-grid">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-10 lg:px-8">
        <section className="grid gap-8 lg:grid-cols-[1.05fr,0.95fr] lg:items-center">
          <div className="space-y-6">
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-zinc-300">
              PRIV Platform Access
            </p>
            <div className="space-y-4">
              <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
                Open the PRIV platform directly from the site, with the Broker Terminal preview ready to go.
              </h1>
              <p className="max-w-2xl text-base leading-7 text-zinc-300 sm:text-lg">
                This landing page gives visitors a fast way into the app, while the embedded preview defaults to the Broker Terminal so the platform can be discovered immediately from the homepage.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                to="/dashboard"
                className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-zinc-200"
              >
                Open platform
              </Link>
              <Link
                to="/dashboard/terminal"
                className="rounded-lg border border-white/15 px-5 py-3 text-sm font-semibold text-white transition hover:border-white/40"
              >
                Open Broker Terminal
              </Link>
              <Link
                to="/dashboard/broker"
                className="rounded-lg border border-white/15 px-5 py-3 text-sm font-semibold text-white transition hover:border-white/40"
              >
                Broker accounts
              </Link>
            </div>

            <div className="grid gap-3 pt-2 sm:grid-cols-3">
              {featureCards.map((card) => (
                <Link
                  key={card.title}
                  to={card.href}
                  className="rounded-xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-white/25 hover:bg-white/[0.04]"
                >
                  <p className="text-sm font-semibold text-white">{card.title}</p>
                  <p className="mt-2 text-sm leading-6 text-zinc-300">{card.desc}</p>
                </Link>
              ))}
            </div>
          </div>

          <div className="glass-morphism rounded-2xl p-3">
            <div className="flex items-center justify-between gap-3 border-b border-white/10 px-3 pb-3">
              <div>
                <p className="text-sm font-semibold text-white">Embedded platform preview</p>
                <p className="text-sm text-zinc-300">Default view: Broker Terminal</p>
              </div>
              <Link
                to="/dashboard/terminal"
                className="rounded-lg border border-white/15 px-3 py-2 text-sm font-semibold text-white transition hover:border-white/40"
              >
                Open full view
              </Link>
            </div>
            <div className="mt-3 overflow-hidden rounded-xl border border-white/10 bg-black">
              <iframe
                src={previewUrl}
                title="PRIV Broker Terminal preview"
                className="h-[420px] w-full border-0"
                loading="lazy"
                allow="clipboard-write; fullscreen"
              />
            </div>
            <div className="mt-3 flex justify-end">
              <Link
                to="/dashboard"
                className="text-sm font-semibold text-zinc-200 underline-offset-4 transition hover:text-white hover:underline"
              >
                Open full dashboard
              </Link>
            </div>
          </div>
        </section>

        <section className="grid gap-4 border-t border-white/10 pt-6 sm:grid-cols-3">
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <p className="text-sm font-semibold text-white">Direct route access</p>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              Every CTA on this page links to an existing app route, so crawlers and visitors can reach the same platform from the homepage.
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <p className="text-sm font-semibold text-white">Preview-first discovery</p>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              The embedded preview opens on the Broker Terminal so visitors immediately see the operational surface of the platform.
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <p className="text-sm font-semibold text-white">Crawl-ready navigation</p>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              The homepage now exposes real routes for discovery, which is the most reliable way to integrate platform access into the sitemap-driven crawl path.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
