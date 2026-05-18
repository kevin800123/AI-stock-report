import { createContext, useContext } from 'react'

import { useBackendWake } from '../hooks/useBackendWake.js'

const BackendWakeContext = createContext(null)

export function BackendWakeProvider({ children, onWakeSuccess }) {
  const value = useBackendWake({ onWakeSuccess })
  return <BackendWakeContext.Provider value={value}>{children}</BackendWakeContext.Provider>
}

export function useBackendWakeContext() {
  const ctx = useContext(BackendWakeContext)
  if (!ctx) {
    throw new Error('useBackendWakeContext must be used within BackendWakeProvider')
  }
  return ctx
}
