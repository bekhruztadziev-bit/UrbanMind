import { useState, useEffect, useRef } from 'react'

/**
 * URBANMIND Centralized Motion Tokens (URBANMIND_MOTION_SYSTEM_006)
 * Precise, analytical, state-driven motion system based on Web Animations API.
 */
export const MOTION = {
  instant: 120,
  fast: 200,
  normal: 360,
  emphasis: 520,
  reveal: 650,
  staggerSmall: 65,
  staggerMedium: 95,
  easeStandard: 'cubic-bezier(0.2, 0, 0, 1)',
  easeEmphasized: 'cubic-bezier(0.16, 1, 0.3, 1)',
  easeExit: 'cubic-bezier(0.4, 0, 1, 1)',
}

/**
 * Detect user's reduced-motion preference.
 */
export const isReducedMotion = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Animate single element entering smoothly into view with fill: 'both'.
 * @param {HTMLElement} element - Target DOM element
 * @param {Object} options - Optional animation parameters
 */
export const animateEnter = (element, options = {}) => {
  if (!element || isReducedMotion()) return null

  const {
    delay = 0,
    duration = MOTION.normal,
    y = 18,
    easing = MOTION.easeEmphasized,
    fill = 'both',
  } = typeof options === 'number' ? { delay: options } : options

  try {
    return element.animate([
      { opacity: 0, transform: `translateY(${y}px)` },
      { opacity: 1, transform: 'translateY(0)' },
    ], {
      duration,
      delay,
      easing,
      fill,
    })
  } catch (err) {
    return null
  }
}

/**
 * Animate multiple elements with progressive staggered entrance.
 * @param {Array<HTMLElement>|NodeList} elements - List of DOM elements
 * @param {Object|number} options - Stagger options or baseDelay number
 */
export const staggerEnter = (elements, options = {}) => {
  if (!elements || isReducedMotion()) return []

  const {
    baseDelay = MOTION.staggerSmall,
    duration = MOTION.normal,
    y = 14,
    easing = MOTION.easeEmphasized,
    fill = 'both',
  } = typeof options === 'number' ? { baseDelay: options } : options

  const list = Array.isArray(elements) ? elements : Array.from(elements || [])
  const animations = []

  list.forEach((el, index) => {
    if (el) {
      const anim = animateEnter(el, {
        delay: index * baseDelay,
        duration,
        y,
        easing,
        fill,
      })
      if (anim) animations.push(anim)
    }
  })

  return animations
}

/**
 * Animate element exiting view smoothly.
 * @param {HTMLElement} element - Target DOM element
 * @param {Object} options - Exit options
 */
export const animateExit = (element, options = {}) => {
  if (!element || isReducedMotion()) return null

  const {
    duration = MOTION.fast,
    y = -6,
    easing = MOTION.easeExit,
    fill = 'forwards',
  } = options

  try {
    return element.animate([
      { opacity: 1, transform: 'translateY(0)' },
      { opacity: 0, transform: `translateY(${y}px)` },
    ], {
      duration,
      easing,
      fill,
    })
  } catch (err) {
    return null
  }
}

/**
 * Briefly highlight an element when selected or modified (single non-repeating pulse).
 * @param {HTMLElement} element - Target DOM element
 * @param {Object} options - Highlight options
 */
export const animateHighlight = (element, options = {}) => {
  if (!element || isReducedMotion()) return null

  const {
    duration = MOTION.emphasis,
    easing = MOTION.easeEmphasized,
    accentColor = 'rgba(56, 189, 248, 0.7)',
    glowColor = 'rgba(56, 189, 248, 0.12)',
  } = options

  try {
    return element.animate([
      { borderColor: accentColor, backgroundColor: glowColor, transform: 'scale(1.02)' },
      { borderColor: 'var(--border-color)', backgroundColor: 'transparent', transform: 'scale(1)' },
    ], {
      duration,
      easing,
    })
  } catch (err) {
    return null
  }
}

/**
 * Token/Badge state change highlight (duration < 500ms).
 */
export const animateTokenFlash = (element) => {
  if (!element || isReducedMotion()) return null

  try {
    return element.animate([
      { opacity: 0.5, transform: 'scale(0.92)' },
      { opacity: 1, transform: 'scale(1.08)', filter: 'brightness(1.3)' },
      { opacity: 1, transform: 'scale(1)', filter: 'brightness(1)' },
    ], {
      duration: MOTION.normal,
      easing: MOTION.easeEmphasized,
    })
  } catch (err) {
    return null
  }
}

/**
 * React Hook for smooth numerical value transitions.
 * Transition: previous value -> smooth numerical interpolation -> new value -> settle.
 * Does NOT continuously animate static values.
 *
 * @param {number} targetValue - Destination value
 * @param {number} decimals - Precision decimals
 * @param {number} duration - Interpolation duration in ms
 */
export function useAnimatedNumber(targetValue, decimals = 0, duration = MOTION.reveal) {
  const numTarget = typeof targetValue === 'number' && !isNaN(targetValue) ? targetValue : 0
  const [displayValue, setDisplayValue] = useState(0)
  const prevValueRef = useRef(0)
  const animRef = useRef(null)

  useEffect(() => {
    const startVal = prevValueRef.current
    const endVal = numTarget

    if (isReducedMotion()) {
      setDisplayValue(endVal)
      prevValueRef.current = endVal
      return
    }

    const startTime = performance.now()
    if (animRef.current) cancelAnimationFrame(animRef.current)

    const updateNumber = (now) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic curve for visible and smooth numeric counting
      const ease = 1 - Math.pow(1 - progress, 3)
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
