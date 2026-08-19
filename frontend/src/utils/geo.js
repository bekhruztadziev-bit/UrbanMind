export function getMapBounds(mahalla) {
  const bounds = mahalla?.bounds
  if (!bounds) return null
  return [bounds.southwest, bounds.northeast]
}

export function getCityBounds(mahalla) {
  const cityBounds = mahalla?.urban_context?.display_bounds
  if (!cityBounds) return getMapBounds(mahalla)
  return [cityBounds.southwest, cityBounds.northeast]
}

export function getBoundaryCube(mahalla) {
  const bounds = mahalla?.bounds
  if (!bounds?.southwest || !bounds?.northeast) return null
  
  const sw = [bounds.southwest[0], bounds.southwest[1]]
  const ne = [bounds.northeast[0], bounds.northeast[1]]
  
  const latSpan = ne[0] - sw[0]
  const lngSpan = ne[1] - sw[1]
  const skewLat = latSpan * 0.18
  const skewLng = lngSpan * 0.18

  const topLeft = [sw[0] + latSpan * 0.06, sw[1] + lngSpan * 0.08]
  const topRight = [ne[0] + latSpan * 0.06, sw[1] + lngSpan * 0.08]
  const farRight = [ne[0] + skewLat, ne[1] + skewLng]
  const farLeft = [sw[0] - skewLat, ne[1] - skewLng]
  const bottomLeft = [sw[0], sw[1]]
  const bottomRight = [ne[0], ne[1]]

  return {
    outer: [
      bottomLeft,
      topLeft,
      topRight,
      farRight,
      bottomRight,
      farLeft,
    ],
    inner: [
      [bottomLeft[0] + latSpan * 0.12, bottomLeft[1] + lngSpan * 0.12],
      [topLeft[0] + latSpan * 0.08, topLeft[1] + lngSpan * 0.08],
      [topRight[0] + latSpan * 0.08, topRight[1] + lngSpan * 0.08],
      [farRight[0] - skewLat * 0.12, farRight[1] - skewLng * 0.12],
      [bottomRight[0] - latSpan * 0.12, bottomRight[1] - lngSpan * 0.12],
      [farLeft[0] + skewLat * 0.12, farLeft[1] + skewLng * 0.12],
    ],
  }
}

export function getFlowDots(mahalla) {
  if (!mahalla?.roads) return []

  const points = []

  mahalla.roads.forEach((road, roadIndex) => {
    for (let i = 0; i < road.length - 1; i += 1) {
      const start = road[i]
      const end = road[i + 1]
      const totalSteps = Math.max(18, Math.round(Math.hypot(end[0] - start[0], end[1] - start[1]) * 9000))

      for (let step = 0; step <= totalSteps; step += 1) {
        const ratio = step / totalSteps
        const lat = start[0] + (end[0] - start[0]) * ratio
        const lng = start[1] + (end[1] - start[1]) * ratio
        const laneOffset = (roadIndex % 2 === 0 ? 1 : -1) * 0.00008
        const offsetAngle = ((roadIndex % 3) + 1) * 0.35
        const offsetLat = Math.cos(offsetAngle) * laneOffset
        const offsetLng = Math.sin(offsetAngle) * laneOffset

        points.push({
          id: `road-${roadIndex}-segment-${i}-dot-${step}`,
          coords: [lat + offsetLat, lng + offsetLng],
          radius: 2.2 + ((step + roadIndex) % 3) * 0.35,
        })
      }
    }
  })

  return points
}
