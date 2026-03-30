"use client";

import React, { useRef, useState, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Sphere, Line, OrbitControls, Text } from "@react-three/drei";
import * as THREE from "three";

/**
 * CentralPatientNode Component
 * Renders the large central sphere representing the current patient.
 * Gently rotates to indicate the focal point of the analysis.
 */
function CentralPatientNode() {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  // Gentle pulsing (no rotation)
  useFrame(({ clock }) => {
    if (glowRef.current) {
      const scale = 1 + Math.sin(clock.getElapsedTime() * 1.5) * 0.15;
      glowRef.current.scale.set(scale, scale, scale);
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Core patient sphere - white with cyan emissive */}
      <Sphere ref={meshRef} args={[0.6, 64, 64]}>
        <meshStandardMaterial
          color="#e2e8f0"
          emissive="#38bdf8"
          emissiveIntensity={0.5}
          metalness={0.3}
          roughness={0.3}
        />
      </Sphere>

      {/* Breathing glow aura around patient */}
      <Sphere ref={glowRef} args={[0.75, 32, 32]}>
        <meshBasicMaterial
          color="#38bdf8"
          transparent
          opacity={0.08}
        />
      </Sphere>

      {/* Label: "Current Patient" */}
      <Text
        position={[0, 1.1, 0]}
        fontSize={0.25}
        color="#e2e8f0"
        anchorX="center"
        anchorY="middle"
        fontWeight="800"
        maxWidth={2}
      >
        Current Patient
      </Text>
    </group>
  );
}

interface RiskFactorNodeProps {
  position: [number, number, number];
  name: string;
  isContributing: boolean;
}

/**
 * RiskFactorNode Component
 * Renders a single epidemiological risk factor sphere.
 * Pulses with pink when flagged (contributing to resistance), calm blue otherwise.
 */
function RiskFactorNode({ position, name, isContributing }: RiskFactorNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    // Pulse animation for contributing factors
    if (isContributing && glowRef.current) {
      const pulseIntensity = Math.sin(clock.getElapsedTime() * 2) * 0.5 + 0.5;
      glowRef.current.material.opacity = 0.2 * pulseIntensity;
    }

    // Emissive intensity pulse for contributing factors
    if (isContributing && meshRef.current) {
      const emissivePulse = Math.sin(clock.getElapsedTime() * 2.5) * 0.3 + 0.6;
      (meshRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        emissivePulse;
    }
  });

  return (
    <group position={position}>
      {/* Core sphere */}
      <Sphere ref={meshRef} args={[0.35, 48, 48]}>
        <meshStandardMaterial
          color={isContributing ? "#ffffff" : "#38bdf8"}
          emissive={isContributing ? "#f472b6" : "#0f172a"}
          emissiveIntensity={isContributing ? 0.6 : 0.1}
          metalness={0.5}
          roughness={0.3}
        />
      </Sphere>

      {/* Glowing aura for contributing factors */}
      {isContributing && (
        <Sphere ref={glowRef} args={[0.52, 32, 32]}>
          <meshBasicMaterial
            color="#f472b6"
            transparent
            opacity={0.2}
          />
        </Sphere>
      )}

      {/* Subtle glow for non-contributing factors */}
      {!isContributing && (
        <Sphere args={[0.48, 32, 32]}>
          <meshBasicMaterial
            color="#38bdf8"
            transparent
            opacity={0.08}
          />
        </Sphere>
      )}

      {/* Risk Factor Label */}
      <Text
        position={[0, isContributing ? 0.65 : 0.6, 0]}
        fontSize={0.16}
        color={isContributing ? "#f472b6" : "#cbd5e1"}
        anchorX="center"
        anchorY="middle"
        fontWeight="700"
        maxWidth={1}
      >
        {name}
      </Text>
    </group>
  );
}

interface EdgeProps {
  from: [number, number, number];
  to: [number, number, number];
  isActive: boolean;
}

/**
 * Edge Component
 * Renders a line connecting central patient to risk factor.
 * Glows pink when the risk factor is contributing, subtle blue otherwise.
 */
function Edge({ from, to, isActive }: EdgeProps) {
  const lineRef = useRef<THREE.LineSegments>(null);

  useFrame(({ clock }) => {
    if (isActive && lineRef.current) {
      const glow = Math.sin(clock.getElapsedTime() * 2.5) * 0.25 + 0.5;
      const material = lineRef.current.material as THREE.LineBasicMaterial;
      material.opacity = 0.4 + glow * 0.3;
    }
  });

  return (
    <Line
      ref={lineRef}
      points={[from, to]}
      color={isActive ? "#f472b6" : "#475569"}
      lineWidth={isActive ? 1.5 : 0.8}
      transparent
      opacity={isActive ? 0.6 : 0.25}
    />
  );
}

interface SceneProps {
  flaggedGenes?: string[];  // Contains risk factor names that are contributing
}

/**
 * Scene Component
 * Renders a professional epidemiological patient risk profile visualization.
 * Central patient node connected to 6 risk factor nodes (hexagon arrangement) with interactive visualization.
 */
export default function Scene({ flaggedGenes = [] }: SceneProps) {
  // Define the 6 epidemiological risk factors positioned in hexagon around central patient
  // 6 nodes evenly spaced at 60° intervals, radius 3.5 units
  const riskFactors = [
    { name: "Age", position: [3.5, 0, 0] as [number, number, number] },
    { name: "Gender", position: [1.75, 3.03, 0] as [number, number, number] },
    { name: "Diabetes", position: [-1.75, 3.03, 0] as [number, number, number] },
    { name: "Hospital_before", position: [-3.5, 0, 0] as [number, number, number] },
    { name: "Hypertension", position: [-1.75, -3.03, 0] as [number, number, number] },
    { name: "Infection_Freq", position: [1.75, -3.03, 0] as [number, number, number] },
  ];

  // Central patient position
  const centerPos: [number, number, number] = [0, 0, 0];

  return (
    <Canvas
      camera={{ position: [8, 8, 8], fov: 50 }}
      className="w-full h-full bg-gradient-to-b from-slate-950 to-slate-900"
      onWheel={(e) => e.preventDefault()}
    >
      {/* Lighting Setup */}
      
      {/* Ambient light - base illumination */}
      <ambientLight intensity={0.4} />

      {/* Primary white directional light */}
      <directionalLight
        position={[10, 10, 10]}
        intensity={0.8}
        color="#ffffff"
        castShadow
      />

      {/* Soft cyan accent light from left */}
      <pointLight position={[-12, 5, 8]} intensity={0.4} color="#38bdf8" />

      {/* Soft pink accent light from right */}
      <pointLight position={[12, -5, 8]} intensity={0.3} color="#f472b6" />

      {/* Cool blue back-light */}
      <pointLight position={[0, 0, -15]} intensity={0.25} color="#1e293b" />

      {/* Scene Content */}
      
      {/* Central Patient Node */}
      <CentralPatientNode />

      {/* Risk Factor Nodes */}
      {riskFactors.map((factor) => (
        <RiskFactorNode
          key={factor.name}
          position={factor.position}
          name={factor.name}
          isContributing={flaggedGenes.includes(factor.name)}
        />
      ))}

      {/* Connecting Edges (Center to Each Risk Factor) */}
      {riskFactors.map((factor) => (
        <Edge
          key={`edge-${factor.name}`}
          from={centerPos}
          to={factor.position}
          isActive={flaggedGenes.includes(factor.name)}
        />
      ))}

      {/* Interactive Controls - Click-to-Rotate with Isometric View */}
      <OrbitControls
        autoRotate={false}
        enableZoom={false}
        enablePan={false}
        minDistance={15}
        maxDistance={15}
        rotateSpeed={1}
        dampingFactor={0.05}
        autoRotateSpeed={0}
        enableDamping={true}
      />

      {/* Subtle background grid for depth reference */}
      <gridHelper
        args={[40, 40]}
        position={[0, -5, 0]}
      />
    </Canvas>
  );
}
