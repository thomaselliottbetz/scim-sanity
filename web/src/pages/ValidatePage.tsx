import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Alert from '@cloudscape-design/components/alert'
import Button from '@cloudscape-design/components/button'
import Container from '@cloudscape-design/components/container'
import ContentLayout from '@cloudscape-design/components/content-layout'
import FormField from '@cloudscape-design/components/form-field'
import Grid from '@cloudscape-design/components/grid'
import Header from '@cloudscape-design/components/header'
import Select, { type SelectProps } from '@cloudscape-design/components/select'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Spinner from '@cloudscape-design/components/spinner'
import Toggle from '@cloudscape-design/components/toggle'
import { fetchExamples, validatePayload, type Example, type ValidateResponse } from '../api/client'
import JsonEditor from '../components/JsonEditor'
import ValidationResults from '../components/ValidationResults'

export default function ValidatePage() {
  const [searchParams] = useSearchParams()
  const [json, setJson] = useState('')
  const [operation, setOperation] = useState<'full' | 'patch'>('full')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [examples, setExamples] = useState<Example[]>([])
  const [selectedOption, setSelectedOption] = useState<SelectProps.Option | null>(null)

  useEffect(() => {
    document.title = 'Validate — scim-sanity'
  }, [])

  useEffect(() => {
    fetchExamples()
      .then(setExamples)
      .catch(() => {
        // Examples are optional on Validate — silently ignore fetch failures
      })
  }, [])

  // Pre-load example when navigated from the Examples page (?example=<id>)
  useEffect(() => {
    const exampleId = searchParams.get('example')
    if (!exampleId || examples.length === 0) return
    const example = examples.find((e) => e.id === exampleId)
    if (!example) return
    setJson(JSON.stringify(example.payload, null, 2))
    setOperation(example.operation)
    setSelectedOption({ value: example.id, label: example.name })
    setResult(null)
    setParseError(null)
    setApiError(null)
  }, [examples, searchParams])

  function handleExampleSelect(option: SelectProps.Option) {
    setSelectedOption(option)
    const example = examples.find((e) => e.id === option.value)
    if (!example) return
    setJson(JSON.stringify(example.payload, null, 2))
    setOperation(example.operation)
    setResult(null)
    setParseError(null)
    setApiError(null)
  }

  async function handleValidate() {
    setParseError(null)
    setResult(null)
    setApiError(null)

    let parsed: unknown
    try {
      parsed = JSON.parse(json)
    } catch (e) {
      setParseError(`Invalid JSON — ${(e as Error).message}`)
      return
    }

    setLoading(true)
    try {
      const data = await validatePayload(parsed, operation)
      setResult(data)
    } catch (e) {
      setApiError(`Request failed — ${(e as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  const exampleOptions: SelectProps.Option[] = examples.map((e) => ({
    value: e.id,
    label: e.name,
    description: e.resource_type,
  }))

  return (
    <ContentLayout header={<Header variant="h1">Validate</Header>}>
      <SpaceBetween size="l">
        <Container>
          <SpaceBetween size="m" direction="horizontal">
            <FormField label="Load example">
              <Select
                selectedOption={selectedOption}
                onChange={({ detail }) => handleExampleSelect(detail.selectedOption)}
                options={exampleOptions}
                placeholder="Choose an example…"
                empty="No examples available"
              />
            </FormField>
            <FormField label="Operation">
              <Toggle
                checked={operation === 'patch'}
                onChange={({ detail }) => setOperation(detail.checked ? 'patch' : 'full')}
              >
                PATCH operation
              </Toggle>
            </FormField>
          </SpaceBetween>
        </Container>

        <Grid gridDefinition={[{ colspan: { default: 12, l: 7 } }, { colspan: { default: 12, l: 5 } }]}>
          {/* Left: editor + button */}
          <SpaceBetween size="s">
            <JsonEditor value={json} onChange={setJson} />
            <Button
              variant="primary"
              onClick={() => void handleValidate()}
              disabled={loading || json.trim() === ''}
            >
              Validate
            </Button>
          </SpaceBetween>

          {/* Right: results */}
          <div>
            {loading && <Spinner size="large" />}
            {!loading && parseError && (
              <Alert type="error" header="Invalid JSON">
                {parseError}
              </Alert>
            )}
            {!loading && apiError && (
              <Alert type="error" header="Request failed">
                {apiError}
              </Alert>
            )}
            {!loading && result && (
              <ValidationResults valid={result.valid} errors={result.errors} />
            )}
          </div>
        </Grid>
      </SpaceBetween>
    </ContentLayout>
  )
}
