
import React from "react"

const SITE = {
  title: "Avatar AI",
  tagline: "Adaptive AI Identity",
  description: "Adaptive AI avatar system for immersive identity and presence across digital experiences.",
  features: ["AI identity", "Presence simulation", "Emotion-aware responses", "Avatar continuity"]
}

export default function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#07101f', color: '#f7f3e8', fontFamily: 'Inter,system-ui, sans-serif', padding: '28px', display: 'flex', flexDirection: 'column', gap: 28 }}>
      <section style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 980, width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
          <div>
            <div style={{ fontSize: '0.8rem', letterSpacing: '0.35em', textTransform: 'uppercase', color: '#d6ba6c', marginBottom: 8 }}>{SITE.title}</div>
            <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4.5rem)', margin: 0, lineHeight: 1.05 }}>{SITE.tagline}</h1>
          </div>
          <div style={{ minWidth: 180, padding: '14px 20px', borderRadius: 18, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(214,186,108,0.18)' }}>
            <div style={{ fontSize: '0.75rem', color: '#c9b570', textTransform: 'uppercase', letterSpacing: '0.22em', marginBottom: 8 }}>System Status</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>Ready</div>
          </div>
        </div>
        <p style={{ fontSize: '1rem', lineHeight: 1.8, color: '#ccc', maxWidth: '42rem' }}>{SITE.description}</p>
      </section>
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 16, width: '100%' }}>
        {SITE.features.map(feature => (
          <div key={feature} style={{ padding: '22px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.02)' }}>
            <div style={{ fontSize: '0.85rem', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#d6ba6c', marginBottom: 10 }}>Feature</div>
            <div style={{ fontSize: '1.1rem', lineHeight: 1.6 }}>{feature}</div>
          </div>
        ))}
      </section>
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 24, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, color: '#9d9582' }}>
        <div>React + Vite scaffold created for "Avatar AI".</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ padding: '10px 16px', borderRadius: 999, border: '1px solid rgba(214,186,108,0.2)', background: 'rgba(255,255,255,0.04)' }}>Deploy Ready</span>
          <span style={{ padding: '10px 16px', borderRadius: 999, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(22,34,50,0.85)' }}>Vite</span>
        </div>
      </footer>
    </div>
  )
}
