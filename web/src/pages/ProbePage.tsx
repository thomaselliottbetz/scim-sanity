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
import ExpandableSection from '@cloudscape-design/components/expandable-section'
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

const PROFILE_OPTIONS: SelectProps.Option[] = [
  { value: '', label: 'None' },
  { value: 'entra', label: 'entra — Microsoft Entra ID' },
  { value: 'fortiauthenticator', label: 'fortiauthenticator — FortiAuthenticator' },
]

export default function ProbePage() {
  const [url, setUrl] = useState('')
  const [authType, setAuthType] = useState<'bearer' | 'basic'>('bearer')
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [strict, setStrict] = useState(true)
  const [profile, setProfile] = useState<SelectProps.Option>(PROFILE_OPTIONS[0])
  const [userDomain, setUserDomain] = useState('')
  const [resource, setResource] = useState<SelectProps.Option>(RESOURCE_OPTIONS[0])
  const [tlsNoVerify, setTlsNoVerify] = useState(false)
  const [skipCleanup, setSkipCleanup] = useState(false)
  const [timeoutSecs, setTimeoutSecs] = useState('30')
  const [proxy, setProxy] = useState('')
  const [caBundle, setCaBundle] = useState('')
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
        profile: profile.value || undefined,
        user_domain: profile.value === 'entra' && userDomain.trim() ? userDomain.trim() : undefined,
        proxy: proxy.trim() || undefined,
        ca_bundle: caBundle.trim() || undefined,
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
              <FormField
                label="Mode"
                description={profile.value && strict ? 'Compat mode recommended for this profile' : undefined}
              >
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

            <SpaceBetween size="l" direction="horizontal">
              <FormField label="Server profile" description="Injects required non-RFC fields for known servers">
                <Select
                  selectedOption={profile}
                  onChange={({ detail }) => {
                    const val = detail.selectedOption.value
                    setProfile(detail.selectedOption)
                    if (val !== 'entra') setUserDomain('')
                    if (val === 'entra' || val === 'fortiauthenticator') setStrict(false)
                  }}
                  options={PROFILE_OPTIONS}
                />
              </FormField>

              {profile.value === 'entra' && (
                <FormField label="User domain" description="e.g. tenant.onmicrosoft.com">
                  <Input
                    value={userDomain}
                    onChange={({ detail }) => setUserDomain(detail.value)}
                    placeholder="tenant.onmicrosoft.com"
                  />
                </FormField>
              )}
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

            <ExpandableSection headerText="Advanced" defaultExpanded={false}>
              <SpaceBetween size="l">
                <FormField
                  label="Proxy URL"
                  description="Routes probe traffic through this proxy. Pass explicitly — env vars (HTTPS_PROXY etc.) are not inherited. Credentials in URL are supported: http://user:pass@proxy:8080"
                >
                  <Input
                    value={proxy}
                    onChange={({ detail }) => setProxy(detail.value)}
                    placeholder="http://proxy.example.com:8080"
                  />
                </FormField>
                <FormField
                  label="CA bundle path (server/container path)"
                  description="Path to a CA bundle file on the machine running scim-sanity. In container deployments, mount the bundle into the container and provide the in-container path. Alternatively, set REQUESTS_CA_BUNDLE or SSL_CERT_FILE env vars on the server — requests honours these automatically without needing this field."
                >
                  <Input
                    value={caBundle}
                    onChange={({ detail }) => setCaBundle(detail.value)}
                    placeholder="/path/to/ca-cert.pem"
                  />
                </FormField>
              </SpaceBetween>
            </ExpandableSection>

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
