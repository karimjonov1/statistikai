import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { ContactShadows, Environment, Float, Sparkles } from '@react-three/drei'
import * as THREE from 'three'

export function Experience() {
  const groupRef = useRef<THREE.Group>(null)
  const mainMeshRef = useRef<THREE.Mesh>(null)

  useFrame((state, delta) => {
    if (!groupRef.current || !mainMeshRef.current) return

    // Subtle parallax based on pointer
    const targetRotX = THREE.MathUtils.clamp(-state.pointer.y * 0.6, -0.6, 0.6)
    const targetRotY = THREE.MathUtils.clamp(state.pointer.x * 1.0, -1.0, 1.0)

    groupRef.current.rotation.x = THREE.MathUtils.lerp(
      groupRef.current.rotation.x,
      targetRotX,
      0.05
    )
    groupRef.current.rotation.y = THREE.MathUtils.lerp(
      groupRef.current.rotation.y,
      targetRotY,
      0.05
    )

    // Idle rotation
    mainMeshRef.current.rotation.y += delta * 0.3
  })

  return (
    <group ref={groupRef} position={[0, 0.2, 0]}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[2, 3, 2]} intensity={1.2} castShadow />

      <Float speed={1.2} floatIntensity={1.6} rotationIntensity={1.2}>
        <mesh ref={mainMeshRef} castShadow>
          <icosahedronGeometry args={[1.2, 1]} />
          <meshStandardMaterial color={'#72e7ff'} metalness={0.5} roughness={0.15} />
        </mesh>
      </Float>

      <Sparkles count={80} scale={[8, 4, 8]} size={2} speed={0.6} opacity={0.6} />

      {/* Ground & shadows */}
      <mesh position={[0, -1.25, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[8, 64]} />
        <meshStandardMaterial color={'#111'} roughness={1} metalness={0} />
      </mesh>
      <ContactShadows
        position={[0, -1.2, 0]}
        opacity={0.5}
        scale={10}
        blur={2.5}
        far={3.5}
      />

      <Environment preset="city" />
    </group>
  )
}

export default Experience