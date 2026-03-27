import { useState } from 'react'
import Badge from '@cloudscape-design/components/badge'
import Box from '@cloudscape-design/components/box'
import Button from '@cloudscape-design/components/button'
import ExpandableSection from '@cloudscape-design/components/expandable-section'
import SpaceBetween from '@cloudscape-design/components/space-between'
import { type Example } from '../api/client'

interface ExampleCardProps {
  example: Example
  onLoad: (example: Example) => void
}

const RESOURCE_TYPE_COLOR: Record<string, 'blue' | 'green' | 'red' | 'grey' | 'severity-critical'> = {
  User: 'blue',
  Group: 'green',
  Agent: 'severity-critical',
  AgenticApplication: 'red',
  PATCH: 'grey',
}

export default function ExampleCard({ example, onLoad }: ExampleCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <SpaceBetween size="s">
      <SpaceBetween size="xs" direction="horizontal">
        <Badge color={RESOURCE_TYPE_COLOR[example.resource_type] ?? 'grey'}>
          {example.resource_type}
        </Badge>
        <Badge color={example.valid ? 'green' : 'red'}>
          {example.valid ? 'Valid' : 'Invalid'}
        </Badge>
      </SpaceBetween>

      <Box variant="p">{example.description}</Box>

      <Box variant="small" color="text-status-inactive">
        {example.rfc_notes}
      </Box>

      <ExpandableSection
        headerText="Payload"
        expanded={expanded}
        onChange={({ detail }) => setExpanded(detail.expanded)}
        variant="footer"
      >
        <pre
          style={{
            fontFamily: 'monospace',
            fontSize: '12px',
            background: '#f8f8f8',
            padding: '8px',
            borderRadius: '2px',
            overflow: 'auto',
            margin: 0,
          }}
        >
          {JSON.stringify(example.payload, null, 2)}
        </pre>
      </ExpandableSection>

      <Button onClick={() => onLoad(example)}>Load in Validator</Button>
    </SpaceBetween>
  )
}
