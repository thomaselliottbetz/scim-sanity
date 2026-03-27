import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alert from '@cloudscape-design/components/alert'
import Box from '@cloudscape-design/components/box'
import Cards from '@cloudscape-design/components/cards'
import ContentLayout from '@cloudscape-design/components/content-layout'
import Header from '@cloudscape-design/components/header'
import Select, { type SelectProps } from '@cloudscape-design/components/select'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Spinner from '@cloudscape-design/components/spinner'
import { fetchExamples, type Example } from '../api/client'
import ExampleCard from '../components/ExampleCard'

const RESOURCE_TYPE_OPTIONS: SelectProps.Option[] = [
  { value: 'All', label: 'All resource types' },
  { value: 'User', label: 'User' },
  { value: 'Group', label: 'Group' },
  { value: 'Agent', label: 'Agent' },
  { value: 'AgenticApplication', label: 'AgenticApplication' },
  { value: 'PATCH', label: 'PATCH' },
]

const VALIDITY_OPTIONS: SelectProps.Option[] = [
  { value: 'All', label: 'All' },
  { value: 'Valid', label: 'Valid only' },
  { value: 'Invalid', label: 'Invalid only' },
]

export default function ExamplesPage() {
  const navigate = useNavigate()
  const [examples, setExamples] = useState<Example[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [resourceFilter, setResourceFilter] = useState<SelectProps.Option>(RESOURCE_TYPE_OPTIONS[0])
  const [validityFilter, setValidityFilter] = useState<SelectProps.Option>(VALIDITY_OPTIONS[0])

  useEffect(() => {
    document.title = 'Examples — scim-sanity'
  }, [])

  useEffect(() => {
    fetchExamples()
      .then(setExamples)
      .catch((e: unknown) => setFetchError((e as Error).message))
      .finally(() => setLoading(false))
  }, [])

  function handleLoad(example: Example) {
    navigate(`/validate?example=${example.id}`)
  }

  const filtered = examples.filter((e) => {
    const typeMatch = resourceFilter.value === 'All' || e.resource_type === resourceFilter.value
    const validMatch =
      validityFilter.value === 'All' ||
      (validityFilter.value === 'Valid' && e.valid) ||
      (validityFilter.value === 'Invalid' && !e.valid)
    return typeMatch && validMatch
  })

  return (
    <ContentLayout header={<Header variant="h1">Examples</Header>}>
      <SpaceBetween size="l">
        <SpaceBetween size="s" direction="horizontal">
          <Select
            selectedOption={resourceFilter}
            onChange={({ detail }) => setResourceFilter(detail.selectedOption)}
            options={RESOURCE_TYPE_OPTIONS}
          />
          <Select
            selectedOption={validityFilter}
            onChange={({ detail }) => setValidityFilter(detail.selectedOption)}
            options={VALIDITY_OPTIONS}
          />
        </SpaceBetween>

        {fetchError && (
          <Alert type="error" header="Failed to load examples">
            {fetchError}
          </Alert>
        )}

        {loading ? (
          <Spinner size="large" />
        ) : (
          <Cards
            items={filtered}
            trackBy="id"
            cardDefinition={{
              header: (item) => item.name,
              sections: [
                {
                  id: 'content',
                  content: (item) => (
                    <ExampleCard example={item} onLoad={handleLoad} />
                  ),
                },
              ],
            }}
            empty={
              <Box textAlign="center" color="inherit" padding="l">
                No examples match the current filters.
              </Box>
            }
          />
        )}
      </SpaceBetween>
    </ContentLayout>
  )
}
