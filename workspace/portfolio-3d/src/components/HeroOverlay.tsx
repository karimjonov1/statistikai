export default function HeroOverlay() {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div
        style={{
          maxWidth: 960,
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          textAlign: 'center',
          pointerEvents: 'auto',
          color: 'white',
        }}
      >
        <div style={{ fontSize: '0.95rem', letterSpacing: 3, opacity: 0.9 }}>
          PORTFOLIO
        </div>
        <h1
          style={{
            fontSize: 'clamp(2rem, 6vw, 4rem)',
            lineHeight: 1.1,
            margin: 0,
            fontWeight: 800,
            textShadow: '0 10px 40px rgba(0,0,0,0.6)',
          }}
        >
          Hello, I'm <span style={{ color: '#72e7ff' }}>Your Name</span>
        </h1>
        <p
          style={{
            margin: 0,
            opacity: 0.85,
            fontSize: 'clamp(1rem, 2.5vw, 1.2rem)',
          }}
        >
          Front‑End Developer • 3D Enthusiast • Crafting immersive web experiences
        </p>

        <div
          style={{
            marginTop: '0.75rem',
            display: 'flex',
            justifyContent: 'center',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <a
            href="#work"
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 10,
              background: 'linear-gradient(135deg, #72e7ff, #6a7bff)',
              color: 'white',
              textDecoration: 'none',
              fontWeight: 700,
              boxShadow: '0 10px 30px rgba(114,231,255,0.35)',
            }}
          >
            View Work
          </a>
          <a
            href="#contact"
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 10,
              background: 'rgba(0,0,0,0.5)',
              color: 'white',
              textDecoration: 'none',
              fontWeight: 700,
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(6px)',
            }}
          >
            Contact Me
          </a>
        </div>

        <div style={{ position: 'absolute', bottom: 24, left: 0, right: 0 }}>
          <span style={{ opacity: 0.7, fontSize: 12 }}>Scroll to explore</span>
        </div>
      </div>
    </div>
  )
}