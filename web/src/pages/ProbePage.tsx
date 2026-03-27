import { useEffect, useState } from 'react'
import Alert from '@cloudscape-design/components/alert'
import Button from '@cloudscape-design/components/button'
import Checkbox from '@cloudscape-design/components/checkbox'
import Container from '@cloudscape-design/components/container'
import ContentLayout from '@cloudscape-design/components/content-layout'
import FormField from '@cloudscape-design/components/form-field'
import Header from '@cloudscape-design/components/header'
import Input from '@cloudscape-design/components/input'
import RadioGroup from '@cloudscape-design/components/radio-group'
import Select, { type SelectProps } from '@cloudscape-design/components/select'
import SpaceBetween from '@cloudscape-design/components/space-between'
import StatusIndicator from '@cloudscape-design/components/status-indicator'
import Toggle from '@cloudscape-design/components/toggle'
import { probeServer, type ProbeResponse } from '../api/client'
import ProbeResults from '../components/ProbeResults'

const RESOURCE_OPTIONS: SelectProps.Option[] = [
  { value: '', label: 'All resources' },
  { value: 'User', label: 'User' },
  { value: 'Group', label: 'Group' },
  { value: 'Agent', label: 'Agent' },
  { value: 'AgenticApplication', label: 'AgenticApplication' },
]

export default function ProbePage() {
  const [url, setUrl] = useState('')
  const [authType, setAuthType] = useState<'bearer' | 'basic'>('bearer')
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [strict, setStrict] = useState(true)
  const [resource, setResource] = useState<SelectProps.Option>(RESOURCE_OPTIONS[0])
  const [tlsNoVerify, setTlsNoVerify] = useState(false)
  const [skipCleanup, setSkipCleanup] = useState(false)
  const [timeoutSecs, setTimeoutSecs] = useState('30')
  const [consent, setConsent] = useState(false)

  useEffect(() => {
    document.title = 'Probe — scim-sanity'
  }, [])

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProbeResponse | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [urlError, setUrlError] = useState<string | null>(null)
  const [authError, setAuthError] = useState<string | null>(null)

  async function handleRun() {
    // Client-side field validation
    let valid = true
    if (!url.trim()) {
      setUrlError('URL is required')
      valid = false
    } else {
      setUrlError(null)
    }

    if (authType === 'bearer' && !token.trim()) {
      setAuthError('Bearer token is required')
      valid = false
    } else if (authType === 'basic' && (!username.trim() || !password.trim())) {
      setAuthError('Username and password are both required')
      valid = false
    } else {
      setAuthError(null)
    }

    if (!valid) return

    setLoading(true)
    setResult(null)
    setApiError(null)

    try {
      const data = await probeServer({
        url: url.trim(),
        token: authType === 'bearer' ? token.trim() : undefined,
        username: authType === 'basic' ? username.trim() : undefined,
        password: authType === 'basic' ? password.trim() : undefined,
        strict,
        resource: resource.value || undefined,
        tls_no_verify: tlsNoVerify,
        skip_cleanup: skipCleanup,
        timeout: parseInt(timeoutSecs, 10) || 30,
      })
      setResult(data)
    } catch (e) {
      setApiError(`Request failed — ${(e as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ContentLayout header={<Header variant="h1">Probe</Header>}>
      <SpaceBetween size="l">
        <Container header={<Header variant="h2">Configuration</Header>}>
          <SpaceBetween size="l">

            <FormField label="SCIM Server URL" errorText={urlError}>
              <Input
                value={url}
                onChange={({ detail }) => setUrl(detail.value)}
                placeholder="https://example.com/scim/v2"
                type="url"
              />
            </FormField>

            <FormField label="Authentication" errorText={authError}>
              <SpaceBetween size="s">
                <RadioGroup
                  value={authType}
                  onChange={({ detail }) => {
                    setAuthType(detail.value as 'bearer' | 'basic')
                    setAuthError(null)
                  }}
                  items={[
                    { value: 'bearer', label: 'Bearer token' },
                    { value: 'basic', label: 'Basic auth' },
                  ]}
                />
                {authType === 'bearer' && (
                  <Input
                    value={token}
                    onChange={({ detail }) => setToken(detail.value)}
                    placeholder="Bearer token"
                    type="password"
                  />
                )}
                {authType === 'basic' && (
                  <SpaceBetween size="s">
                    <Input
                      value={username}
                      onChange={({ detail }) => setUsername(detail.value)}
                      placeholder="Username"
                    />
                    <Input
                      value={password}
                      onChange={({ detail }) => setPassword(detail.value)}
                      placeholder="Password"
                      type="password"
                    />
                  </SpaceBetween>
                )}
              </SpaceBetween>
            </FormField>

            <SpaceBetween size="l" direction="horizontal">
              <FormField label="Mode">
                <Toggle
                  checked={!strict}
                  onChange={({ detail }) => setStrict(!detail.checked)}
                >
                  Compat mode
                </Toggle>
              </FormField>

              <FormField label="Resource filter">
                <Select
                  selectedOption={resource}
                  onChange={({ detail }) => setResource(detail.selectedOption)}
                  options={RESOURCE_OPTIONS}
                />
              </FormField>

              <FormField label="Timeout (seconds)">
                <Input
                  value={timeoutSecs}
                  onChange={({ detail }) => setTimeoutSecs(detail.value)}
                  type="number"
                />
              </FormField>
            </SpaceBetween>

            <SpaceBetween size="s">
              <Checkbox
                checked={tlsNoVerify}
                onChange={({ detail }) => setTlsNoVerify(detail.checked)}
              >
                Skip TLS certificate verification
              </Checkbox>
              <Checkbox
                checked={skipCleanup}
                onChange={({ detail }) => setSkipCleanup(detail.checked)}
              >
                Skip cleanup (leave test resources on server)
              </Checkbox>
            </SpaceBetween>

            <FormField>
              <Checkbox
                checked={consent}
                onChange={({ detail }) => setConsent(detail.checked)}
              >
                I accept that this probe will create, modify, and delete resources
                on the target server.
              </Checkbox>
            </FormField>

            <Button
              variant="primary"
              onClick={() => void handleRun()}
              disabled={!consent || loading}
            >
              Run Probe
            </Button>

          </SpaceBetween>
        </Container>

        {loading && (
          <StatusIndicator type="loading">
            Probing server… this may take 30+ seconds.
          </StatusIndicator>
        )}

        {!loading && apiError && (
          <Alert type="error" header="Request failed">
            {apiError}
          </Alert>
        )}

        {!loading && result && <ProbeResults result={result} />}

      </SpaceBetween>
    </ContentLayout>
  )
}
