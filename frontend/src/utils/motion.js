import { useState, useEffect, useRef } from 'react'

/**
 * Motion System using Web Animations API and React State Interpolation.
 * Strictly respects prefers-reduced-motion.
 */

export const isReducedMotion = () => {
  if (typeof window === 'undefined') return true
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const defaultTiming = {
  duration: 380,
  easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
  fill: 'forwards'
}

/**
 * Animate single element entering smoothly into view.
 */
export const animateEnter = (element, delay = 0) => {
  if (!element || isReducedMotion()) return null

  return element.animate([
    { opacity: 0, transform: 'translateY(12px)' },
    { opacity: 1, transform: 'translateY(0)' }
  ], {
    ...defaultTiming,
    delay
  })
}

/**
 * Animate multiple elements with progressive staggered entrance.
 */
export const staggerEnter = (elements, baseDelay = 55) => {
  if (!elements || isReducedMotion()) return

  const list = Array.isArray(elements) ? elements : Array.from(elements || [])
  list.forEach((el, index) => {
    if (el) animateEnter(el, index * baseDelay)
  })
}

/**
 * Briefly highlight an element when selected or modified.
 */
export const animateHighlight = (element) => {
  if (!element || isReducedMotion()) return null

  return element.animate([
    { borderColor: 'var(--accent-primary)', backgroundColor: 'var(--accent-primary-glow)' },
    { borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-elevated)' }
  ], {
    duration: 550,
    easing: 'ease-out'
  })
}

/**
 * React Hook for smooth numerical value transitions.
 * Transition: old value -> smooth interpolation -> new value -> settle.
 * Does NOT continuously animate static values.
 */
export function useAnimatedNumber(targetValue, decimals = 0, duration = 450) {
  const numTarget = typeof targetValue === 'number' && !isNaN(targetValue) ? targetValue : 0
  const [displayValue, setDisplayValue] = useState(numTarget)
  const prevValueRef = useRef(numTarget)
  const animRef = useRef(null)

  useEffect(() => {
    const startVal = prevValueRef.current
    const endVal = numTarget

    if (isReducedMotion() || startVal === endVal) {
      setDisplayValue(endVal)
      prevValueRef.current = endVal
      return
    }

    const startTime = performance.now()
    if (animRef.current) cancelAnimationFrame(animRef.current)

    const updateNumber = (now) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out quartic
      const ease = 1 - Math.pow(1 - progress, 4)
      const current = startVal + (endVal - startVal) * ease

      setDisplayValue(current)

      if (progress < 1) {
        animRef.current = requestAnimationFrame(updateNumber)
      } else {
        setDisplayValue(endVal)
        prevValueRef.current = endVal
      }
    }

    animRef.current = requestAnimationFrame(updateNumber)

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [numTarget, decimals, duration])

  return Number(displayValue).toFixed(decimals)
}

