import { useCallback, useEffect, useState } from 'react'

import { pingHealth } from '../api.js'
import { formatApiError } from '../utils/apiErrors.js'

const SLOW_MS = 3000

function withSlowWarning(promise, onSlow) {
  let done = false
  const timer = setTimeout(() => {
    if (!done) onSlow()
  }, SLOW_MS)
  return promise.finally(() => {
    done = true
    clearTimeout(timer)
  })
}

export function useBackendWake({ onWakeSuccess } = {}) {
  const canWakeBackend = import.meta.env.DEV || !!import.meta.env.VITE_API_BASE_URL
  const [wakeBusy, setWakeBusy] = useState(false)
  const [wakeLine, setWakeLine] = useState('')
  const [coldStartBanner, setColdStartBanner] = useState(false)
  const [bannerDismissed, setBannerDismissed] = useState(false)

  const dismissBanner = useCallback(() => {
    setBannerDismissed(true)
    setColdStartBanner(false)
  }, [])

  const handleWakeBackend = useCallback(async () => {
    if (!canWakeBackend) return
    setWakeLine('')
    setWakeBusy(true)
    try {
      await withSlowWarning(pingHealth(), () => setColdStartBanner(true))
      setWakeLine('後端已回應。若剛從休眠喚醒，後續操作會較順；冷啟動時仍可能需要一點時間。')
      setColdStartBanner(false)
      await onWakeSuccess?.()
    } catch (e) {
      setWakeLine('')
      throw e
    } finally {
      setWakeBusy(false)
    }
  }, [canWakeBackend, onWakeSuccess])

  useEffect(() => {
    if (!canWakeBackend) return
    withSlowWarning(
      pingHealth().catch(() => {}),
      () => setColdStartBanner(true),
    )
  }, [canWakeBackend])

  const showColdStartBanner = coldStartBanner && !bannerDismissed && canWakeBackend

  return {
    canWakeBackend,
    wakeBusy,
    wakeLine,
    setWakeLine,
    showColdStartBanner,
    dismissBanner,
    handleWakeBackend,
    withSlowWarning,
  }
}
