// Tries to extract a human-readable message from a non-ok API response.
// FastAPI returns { detail: string } on 422 and 500; falls back to HTTP status.
async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | { msg: string }[] }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => (typeof d === 'object' && 'msg' in d ? d.msg : String(d))).join('; ')
    }
  } catch {
    // ignore JSON parse failure
  }
  return `HTTP ${res.status}`
}

export interface ValidationError {
  message: string
  path?: string
  line?: number
}

export interface ValidateResponse {
  valid: boolean
  errors: ValidationError[]
}

export interface Example {
  id: string
  name: string
  description: string
  resource_type: string
  operation: 'full' | 'patch'
  valid: boolean
  rfc_notes: string
  payload: Record<string, unknown>
}

export async function validatePayload(
  payload: unknown,
  operation: string,
): Promise<ValidateResponse> {
  const res = await fetch('/api/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payload, operation }),
  })
  if (!res.ok) throw new Error(await extractErrorMessage(res))
  return res.json() as Promise<ValidateResponse>
}

export async function fetchExamples(): Promise<Example[]> {
  const res = await fetch('/api/examples')
  if (!res.ok) throw new Error(await extractErrorMessage(res))
  const data = (await res.json()) as { examples: Example[] }
  return data.examples
}

// ---------------------------------------------------------------------------
// Probe
// ---------------------------------------------------------------------------

export interface ProbeTestResult {
  name: string
  status: 'pass' | 'fail' | 'warn' | 'skip' | 'error'
  message?: string
  details?: string
  phase?: string
}

export interface ProbeIssue {
  priority: string
  title: string
  rationale: string
  fix: string
  affected_tests: number
}

export interface ProbeSummary {
  total: number
  passed: number
  failed: number
  warnings: number
  skipped: number
  errors: number
}

export interface ProbeResponse {
  exit_code: number
  mode: string
  version: string
  timestamp: string
  summary: ProbeSummary
  issues: ProbeIssue[]
  results: ProbeTestResult[]
}

export interface ProbeRequest {
  url: string
  token?: string
  username?: string
  password?: string
  strict: boolean
  resource?: string
  tls_no_verify: boolean
  skip_cleanup: boolean
  timeout: number
  profile?: string
  user_domain?: string
  proxy?: string
  ca_bundle?: string
}

export async function probeServer(req: ProbeRequest): Promise<ProbeResponse> {
  const res = await fetch('/api/probe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(await extractErrorMessage(res))
  return res.json() as Promise<ProbeResponse>
}
