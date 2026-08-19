import React, { useEffect, useRef } from 'react'

/**
 * AmbientBackground - High-performance 60fps Urban Digital Twin Background Animation.
 * Renders an ambient grid with pulsing sensor nodes, subtle telemetry particles,
 * and smooth gradient blooms simulating real-time smart city data flow.
 */
export function AmbientBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d', { alpha: true })
    if (!ctx) return

    let animationFrameId
    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
      initNodes()
    }
    window.addEventListener('resize', handleResize)

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Node & Particle System
    let nodes = []
    let particles = []
    const NODE_COUNT = Math.min(32, Math.max(16, Math.floor(width / 60)))
    const PARTICLE_COUNT = Math.min(45, Math.max(20, Math.floor(width / 45)))

    function initNodes() {
      nodes = []
      for (let i = 0; i < NODE_COUNT; i++) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          radius: Math.random() * 2.2 + 1.2,
          pulse: Math.random() * Math.PI * 2,
          pulseSpeed: 0.015 + Math.random() * 0.02,
          color: i % 4 === 0 ? 'rgba(52, 211, 153, ' : i % 3 === 0 ? 'rgba(192, 132, 252, ' : 'rgba(96, 165, 250, '
        })
      }

      particles = []
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.75 + (Math.random() > 0.5 ? 0.3 : -0.3),
          vy: (Math.random() - 0.5) * 0.6,
          length: Math.random() * 18 + 8,
          alpha: Math.random() * 0.45 + 0.15,
          color: Math.random() > 0.3 ? '#3b82f6' : '#10b981'
        })
      }
    }

    initNodes()

    let time = 0
    let mouseX = width / 2
    let mouseY = height / 2
    let targetMouseX = width / 2
    let targetMouseY = height / 2

    const handleMouseMove = (e) => {
      targetMouseX = e.clientX
      targetMouseY = e.clientY
    }
    window.addEventListener('mousemove', handleMouseMove, { passive: true })

    const render = () => {
      time += 0.012
      mouseX += (targetMouseX - mouseX) * 0.05
      mouseY += (targetMouseY - mouseY) * 0.05

      ctx.clearRect(0, 0, width, height)

      // 1. Draw subtle ambient atmospheric glowing blooms
      const grad1 = ctx.createRadialGradient(
        width * 0.25 + Math.sin(time * 0.5) * 60,
        height * 0.35 + Math.cos(time * 0.4) * 40,
        20,
        width * 0.25,
        height * 0.35,
        width * 0.45
      )
      grad1.addColorStop(0, 'rgba(59, 130, 246, 0.07)')
      grad1.addColorStop(0.5, 'rgba(30, 58, 138, 0.03)')
      grad1.addColorStop(1, 'rgba(15, 23, 42, 0)')
      ctx.fillStyle = grad1
      ctx.fillRect(0, 0, width, height)

      const grad2 = ctx.createRadialGradient(
        width * 0.8 + Math.cos(time * 0.6) * 50,
        height * 0.65 + Math.sin(time * 0.5) * 50,
        10,
        width * 0.8,
        height * 0.65,
        width * 0.4
      )
      grad2.addColorStop(0, 'rgba(16, 185, 129, 0.05)')
      grad2.addColorStop(0.6, 'rgba(6, 78, 59, 0.02)')
      grad2.addColorStop(1, 'rgba(15, 23, 42, 0)')
      ctx.fillStyle = grad2
      ctx.fillRect(0, 0, width, height)

      // 2. Connect near nodes with digital telemetry lines
      if (!prefersReducedMotion) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x
            const dy = nodes[i].y - nodes[j].y
            const dist = Math.sqrt(dx * dx + dy * dy)

            if (dist < 140) {
              const alpha = (1 - dist / 140) * 0.16
              ctx.strokeStyle = `rgba(96, 165, 250, ${alpha})`
              ctx.lineWidth = 0.85
              ctx.beginPath()
              ctx.moveTo(nodes[i].x, nodes[i].y)
              ctx.lineTo(nodes[j].x, nodes[j].y)
              ctx.stroke()
            }
          }
        }
      }

      // 3. Render telemetry particles (moving traffic packets)
      if (!prefersReducedMotion) {
        for (let i = 0; i < particles.length; i++) {
          const p = particles[i]
          p.x += p.vx
          p.y += p.vy

          if (p.x < -20) p.x = width + 20
          if (p.x > width + 20) p.x = -20
          if (p.y < -20) p.y = height + 20
          if (p.y > height + 20) p.y = -20

          ctx.strokeStyle = p.color
          ctx.globalAlpha = p.alpha * (0.65 + 0.35 * Math.sin(time * 2 + i))
          ctx.lineWidth = 1.2
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p.x - p.vx * p.length, p.y - p.vy * p.length)
          ctx.stroke()
          ctx.globalAlpha = 1.0
        }
      }

      // 4. Update & Render Sensor Nodes with live pulse rings
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i]

        if (!prefersReducedMotion) {
          node.x += node.vx
          node.y += node.vy
          node.pulse += node.pulseSpeed

          if (node.x < 0 || node.x > width) node.vx *= -1
          if (node.y < 0 || node.y > height) node.vy *= -1
        }

        const pulseScale = Math.sin(node.pulse) * 0.5 + 0.5
        const currentRadius = node.radius + pulseScale * 1.5

        // Outer pulse aura
        ctx.fillStyle = `${node.color}${0.08 + pulseScale * 0.12})`
        ctx.beginPath()
        ctx.arc(node.x, node.y, currentRadius * 3.5, 0, Math.PI * 2)
        ctx.fill()

        // Inner solid core
        ctx.fillStyle = `${node.color}${0.5 + pulseScale * 0.4})`
        ctx.beginPath()
        ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2)
        ctx.fill()
      }

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render)
      }
    }

    render()

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('mousemove', handleMouseMove)
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
    }
  }, [])

  return (
    <div className="ambient-background-container" aria-hidden="true">
      <div className="ambient-grid-overlay" />
      <div className="ambient-radar-beam" />
      <canvas ref={canvasRef} className="ambient-canvas" />
    </div>
  )
}
