"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, Line, OrbitControls, Text } from "@react-three/drei";
import * as THREE from "three";

interface GeneNodeProps {
  position: [number, number, number];
  color: string;
  name: string;
  isFlagged: boolean;
}

/**
 * GeneNode Component
 * Renders a single gene node in the 3D canvas.
 * If flagged, it emits a glowing red/pink color; otherwise, a calm blue.
 */
function GeneNode({ position, color, name, isFlagged }: GeneNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Gentle rotation animation
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.x += 0.003;
      meshRef.current.rotation.y += 0.005;
    }
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[isFlagged ? 0.4 : 0.3, 32, 32]}>
        <meshStandardMaterial
          color={isFlagged ? "#ff1744" : color}
          emissive={isFlagged ? "#ff1744" : "#000000"}
          emissiveIntensity={isFlagged ? 1.5 : 0}
          metalness={0.6}
          roughness={0.3}
        />
      </Sphere>

      {/* Glow effect for flagged genes */}
      {isFlagged && (
        <Sphere args={[0.5, 32, 32]}>
          <meshBasicMaterial color="#ff1744" transparent opacity={0.2} />
        </Sphere>
      )}

      {/* Label positioned above the sphere using @react-three/drei Text */}
      <Text
        position={[0, isFlagged ? 0.7 : 0.6, 0]}
        fontSize={0.2}
        color={isFlagged ? "#ff1744" : "#ffffff"}
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        {name}
      </Text>
    </group>
  );
}

interface SceneProps {
  flaggedGenes?: string[];
}

/**
 * Scene Component
 * Renders a 3D gene network visualization with interactive controls.
 */
export default function Scene({ flaggedGenes = [] }: SceneProps) {
  // Define gene nodes with positions
  const geneNodes = [
    { position: [-3, 2, 0] as [number, number, number], name: "blaCTX-M-15", color: "#60a5fa" },
    { position: [3, 2, 0] as [number, number, number], name: "mecA", color: "#60a5fa" },
    { position: [-1.5, -2, 2] as [number, number, number], name: "tetM", color: "#60a5fa" },
    { position: [1.5, -2, -2] as [number, number, number], name: "rpoB", color: "#60a5fa" },
  ];

  // Define connections between nodes
  const connections = [
    [geneNodes[0].position, geneNodes[1].position],
    [geneNodes[0].position, geneNodes[2].position],
    [geneNodes[1].position, geneNodes[3].position],
    [geneNodes[2].position, geneNodes[3].position],
  ];

  return (
    <Canvas
      camera={{ position: [0, 0, 8], fov: 75 }}
      className="w-full h-full bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900"
    >
      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <pointLight position={[-10, -10, 10]} intensity={0.4} color="#60a5fa" />

      {/* Gene Nodes */}
      {geneNodes.map((node, index) => (
        <GeneNode
          key={index}
          position={node.position}
          color={node.color}
          name={node.name}
          isFlagged={flaggedGenes.includes(node.name)}
        />
      ))}

      {/* Connection Lines */}
      {connections.map((connection, index) => (
        <Line
          key={index}
          points={connection}
          color="#64748b"
          lineWidth={1}
          transparent
          opacity={0.6}
        />
      ))}

      {/* Interactive Controls */}
      <OrbitControls
        autoRotate
        autoRotateSpeed={1}
        enableZoom
        enablePan
        maxDistance={15}
        minDistance={3}
      />

      {/* Background Grid */}
      <gridHelper args={[20, 20]} position={[0, -3, 0]} />
    </Canvas>
  );
}
