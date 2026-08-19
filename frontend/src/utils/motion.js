/**
 * Motion System using Web Animations API
 * Designed to respect prefers-reduced-motion
 */

export const isReducedMotion = () => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const defaultTiming = {
  duration: 300,
  easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
  fill: 'forwards'
}

export const animateEnter = (element, delay = 0) => {
  if (!element || isReducedMotion()) return null

  return element.animate([
    { opacity: 0, transform: 'translateY(10px)' },
    { opacity: 1, transform: 'translateY(0)' }
  ], {
    ...defaultTiming,
    delay
  })
}

export const animateHighlight = (element) => {
  if (!element || isReducedMotion()) return null

  return element.animate([
    { backgroundColor: 'var(--accent-primary-glow)' },
    { backgroundColor: 'transparent' }
  ], {
    duration: 800,
    easing: 'ease-out',
    fill: 'forwards'
  })
}

/**
 * Animates a number transition in a given element.
 * Assumes the element contains the number text.
 */
export const animateNumber = (element, startVal, endVal, duration = 400) => {
  if (!element || isReducedMotion()) {
    element.textContent = endVal.toFixed(2)
    return null
  }

  let startTime = null
  const step = (currentTime) => {
    if (!startTime) startTime = currentTime
    const progress = Math.min((currentTime - startTime) / duration, 1)
    
    // Ease out quart
    const easeProgress = 1 - Math.pow(1 - progress, 4)
    const currentVal = startVal + (endVal - startVal) * easeProgress
    
    element.textContent = currentVal.toFixed(2)
    
    if (progress < 1) {
      window.requestAnimationFrame(step)
    } else {
      element.textContent = endVal.toFixed(2)
    }
  }
  
  window.requestAnimationFrame(step)
}
