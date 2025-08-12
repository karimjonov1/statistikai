import { Canvas } from '@react-three/fiber'
import { PresentationControls } from '@react-three/drei'
import Experience from './components/Experience'
import HeroOverlay from './components/HeroOverlay'

function App() {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 0, 5], fov: 45 }}
        gl={{ antialias: true }}
        style={{ position: 'absolute', inset: 0 }}
      >
        <color attach="background" args={[0.05, 0.06, 0.08]} />

        <PresentationControls
          global
          snap
          rotation={[0, 0, 0]}
          polar={[-Math.PI / 8, Math.PI / 8]}
          azimuth={[-Math.PI / 6, Math.PI / 6]}
        >
          <Experience />
        </PresentationControls>
      </Canvas>

      <HeroOverlay />
    </div>
  )
}

export default App
