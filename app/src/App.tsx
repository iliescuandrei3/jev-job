import { useEffect, useState } from 'react'
import './App.css'

type JobStatus = 'pending' | 'running' | 'completed' | 'failed'

type JobState = {
  status: JobStatus
  task_name: string
  message: string
}

const ACTIVE_JOB_STORAGE_KEY = 'email-refresh-job-id'
const TERMINAL_STATUSES: JobStatus[] = ['completed', 'failed']

function isJobState(value: unknown): value is JobState {
  if (typeof value !== 'object' || value === null) return false

  const state = value as Record<string, unknown>
  return (
    ['pending', 'running', 'completed', 'failed'].includes(String(state.status)) &&
    typeof state.task_name === 'string' &&
    typeof state.message === 'string'
  )
}

function getWebSocketUrl(jobId: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/emails/ws/sync/${encodeURIComponent(jobId)}`
}

function App() {
  const [jobId, setJobId] = useState(
    () => window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY),
  )
  const [jobState, setJobState] = useState<JobState | null>(() =>
    window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY)
      ? {
          status: 'pending',
          task_name: 'Sync emails',
          message: 'Reconnecting to the active refresh…',
        }
      : null,
  )
  const [isStarting, setIsStarting] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const [connectionMessage, setConnectionMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return

    let isDisposed = false
    let reconnectTimer: number | undefined
    let retryDelay = 1000
    let socket: WebSocket | null = null

    const connect = () => {
      if (isDisposed) return

      setConnectionMessage('Connecting to refresh updates…')
      socket = new WebSocket(getWebSocketUrl(jobId))

      socket.onopen = () => {
        retryDelay = 1000
        setConnectionMessage(null)
      }

      socket.onmessage = (event) => {
        let parsed: unknown
        try {
          parsed = JSON.parse(event.data)
        } catch {
          setConnectionMessage('Received an unreadable refresh update.')
          return
        }

        if (!isJobState(parsed)) {
          setConnectionMessage('Received an invalid refresh update.')
          return
        }

        setJobState(parsed)
        if (TERMINAL_STATUSES.includes(parsed.status)) {
          if (window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY) === jobId) {
            window.localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY)
          }
          setJobId(null)
          socket?.close()
        }
      }

      socket.onerror = () => {
        socket?.close()
      }

      socket.onclose = () => {
        if (isDisposed) return

        setConnectionMessage('Connection lost. Reconnecting to refresh updates…')
        reconnectTimer = window.setTimeout(connect, retryDelay)
        retryDelay = Math.min(retryDelay * 2, 10000)
      }
    }

    connect()
    return () => {
      isDisposed = true
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [jobId])

  const setActiveJob = (id: string) => {
    window.localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, id)
    setJobId(id)
    setJobState({
      status: 'pending',
      task_name: 'Sync emails',
      message: 'Refresh queued. Waiting for progress…',
    })
    setRequestError(null)
  }

  const refreshEmails = async () => {
    setIsStarting(true)
    setRequestError(null)
    try {
      const response = await fetch('/emails/refresh', { method: 'POST' })
      const body: unknown = await response.json()

      if (response.status === 409 && typeof body === 'object' && body !== null) {
        const detail = (body as { detail?: unknown }).detail
        if (typeof detail === 'object' && detail !== null) {
          const existingJobId = (detail as { job_id?: unknown }).job_id
          if (typeof existingJobId === 'string') {
            setActiveJob(existingJobId)
            return
          }
        }
      }

      if (!response.ok) {
        throw new Error(`Refresh request failed (${response.status}).`)
      }

      if (
        typeof body !== 'object' ||
        body === null ||
        typeof (body as { job_id?: unknown }).job_id !== 'string'
      ) {
        throw new Error('The server returned an invalid refresh job.')
      }

      setActiveJob((body as { job_id: string }).job_id)
    } catch (error) {
      setRequestError(
        error instanceof Error ? error.message : 'Unable to start email refresh.',
      )
    } finally {
      setIsStarting(false)
    }
  }

  const isBusy =
    isStarting ||
    jobId !== null ||
    (jobState !== null && !TERMINAL_STATUSES.includes(jobState.status))

  return (
    <main className="refresh-page">
      <section className="refresh-panel" aria-labelledby="page-title">
        <span className="eyebrow">Email sync</span>
        <h1 id="page-title">Keep your inbox up to date</h1>
        <p className="intro">
          Start a refresh and follow its progress here. You can start another
          one after this task finishes.
        </p>

        <button
          className="refresh-button"
          type="button"
          onClick={refreshEmails}
          disabled={isBusy}
        >
          {isStarting
            ? 'Starting refresh…'
            : isBusy
              ? 'Refresh in progress'
              : 'Refresh emails'}
        </button>

        <section
          className={`status-card ${jobState?.status ?? 'idle'}`}
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="status-heading">
            <span className="status-indicator" aria-hidden="true" />
            <h2>{jobState?.task_name || 'Refresh status'}</h2>
            {jobState && <span className="status-label">{jobState.status}</span>}
          </div>
          <p>
            {jobState?.message ??
              'No refresh is running. Start one whenever you are ready.'}
          </p>
          {connectionMessage && (
            <p className="connection-message">{connectionMessage}</p>
          )}
          {requestError && <p className="error-message">{requestError}</p>}
        </section>
      </section>
    </main>
  )
}

export default App
