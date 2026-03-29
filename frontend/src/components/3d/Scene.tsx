"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, Line, OrbitControls, Text } from "@react-three/drei";
import * as THREE from "three";

interface RiskNodeProps {
  position: [number, number, number];
  color: string;
  name: string;
  isFlagged: boolean;
}

/**
 * RiskNode Component
 * Renders a single epidemiological risk factor node in the 3D canvas with medical aesthetic.
 * If flagged, displays with a calm pink glow; otherwise, clean soft blue.
 */
function RiskNode({ position, color, name, isFlagged }: RiskNodeProps) {
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
      {/* Core sphere */}
      <Sphere ref={meshRef} args={[isFlagged ? 0.4 : 0.3, 32, 32]}>
        <meshStandardMaterial
          color={isFlagged ? "#ffffff" : "#38bdf8"}
          emissive={isFlagged ? "#f472b6" : "#000000"}
          emissiveIntensity={isFlagged ? 0.8 : 0}
          metalness={0.4}
          roughness={0.4}
        />
      </Sphere>

      {/* Crayon-like aura for flagged risk factors */}
      {isFlagged && (
        <Sphere args={[0.55, 32, 32]}>
          <meshBasicMaterial color="#f472b6" transparent opacity={0.15} />
        </Sphere>
      )}

      {/* Label positioned above the sphere */}
      <Text
        position={[0, isFlagged ? 0.7 : 0.6, 0]}
        fontSize={0.18}
        color={isFlagged ? "#f472b6" : "#e2e8f0"}
        anchorX="center"
        anchorY="middle"
        fontWeight="600"
        maxWidth={1}
      >
        {name}
      </Text>
    </group>
  );
}

interface SceneProps {
  flaggedGenes?: string[];  // Reused prop name for backward compatibility, but now contains risk factors
}

/**
 * Scene Component
 * Renders a premium medical-grade 3D epidemiological patient risk network visualization.
 */
export default function Scene({ flaggedGenes = [] }: SceneProps) {
  // Define epidemiological risk factor nodes with positions (including central "hub" node)
  // These represent common epidemiological factors: Age, Gender, Comorbidities, Hospital History
  const riskNodes = [
    { position: [-3, 2, 0] as [number, number, number], name: "Hospital_before", color: "#38bdf8" },
    { position: [3, 2, 0] as [number, number, number], name: "Age", color: "#38bdf8" },
    { position: [-1.5, -2, 2] as [number, number, number], name: "Diabetes", color: "#38bdf8" },
    { position: [1.5, -2, -2] as [number, number, number], name: "Gender", color: "#38bdf8" },
    { position: [0, 0, -1] as [number, number, number], name: "Patient Risk Profile", color: "#38bdf8" }, // Central hub
  ];

  // Define connections between nodes (all connect to central hub)
  const connections = [
    [riskNodes[0].position, riskNodes[4].position], // Hospital_before -> Patient Risk Profile
    [riskNodes[1].position, riskNodes[4].position], // Age -> Patient Risk Profile
    [riskNodes[2].position, riskNodes[4].position], // Diabetes -> Patient Risk Profile
    [riskNodes[3].position, riskNodes[4].position], // Gender -> Patient Risk Profile
    [riskNodes[0].position, riskNodes[1].position], // Hospital_before <-> Age
    [riskNodes[2].position, riskNodes[3].position], // Diabetes <-> Gender
  ];

  return (
    <Canvas
      camera={{ position: [0, 0, 9], fov: 72 }}
      className="w-full h-full bg-slate-950"
    >
      {/* Ambient light for base illumination */}
      <ambientLight intensity={0.5} />

      {/* Primary white light from above-right */}
      <pointLight position={[8, 8, 8]} intensity={0.9} color="#ffffff" />

      {/* Soft blue accent light */}
      <pointLight position={[10, 10, 10]} intensity={0.5} color="#38bdf8" />

      {/* Soft pink back-light for medical aesthetic */}
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#f472b6" />

      {/* Risk Factor Nodes */}
      {riskNodes.map((node, index) => (
        <RiskNode
          key={index}
          position={node.position}
          color={node.color}
          name={node.name}
          isFlagged={flaggedGenes.includes(node.name)}
        />
      ))}

      {/* Connection Lines - thin, crisp white */}
      {connections.map((connection, index) => (
        <Line
          key={index}
          points={connection}
          color="#ffffff"
          lineWidth={0.5}
          transparent
          opacity={0.3}
        />
      ))}

      {/* Interactive Controls - calm, clinical rotation */}
      <OrbitControls
        autoRotate
        autoRotateSpeed={0.5}
        enableZoom
        enablePan
        maxDistance={20}
        minDistance={4}
      />

      {/* Subtle background grid */}
      <gridHelper args={[30, 30]} position={[0, -4, 0]} />
    </Canvas>
  );
}
