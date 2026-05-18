import { useCallback, useEffect, useRef, useState } from 'react'

import { getReports } from '../api.js'
import { formatApiError } from '../utils/apiErrors.js'
import { hasProcessingReports } from '../utils/reportStatus.js'

const POLL_MS = 5000

export function useReportsPolling() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isPolling, setIsPolling] = useState(false)
  const initialLoad = useRef(true)

  const fetchReports = useCallback(async ({ silent = false } = {}) => {
    if (!silent && initialLoad.current) {
      setLoading(true)
    }
    try {
      const data = await getReports()
      setReports(data || [])
      setError('')
    } catch (e) {
      setError(formatApiError(e))
    } finally {
      if (!silent && initialLoad.current) {
        setLoading(false)
        initialLoad.current = false
      }
    }
  }, [])

  const refresh = useCallback(() => fetchReports({ silent: false }), [fetchReports])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  useEffect(() => {
    const processing = hasProcessingReports(reports)
    setIsPolling(processing)
    if (!processing) return undefined

    const id = setInterval(() => {
      fetchReports({ silent: true })
    }, POLL_MS)
    return () => clearInterval(id)
  }, [reports, fetchReports])

  return { reports, loading, error, refresh, isPolling, fetchReports }
}
