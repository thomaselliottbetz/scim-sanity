import Box from '@cloudscape-design/components/box'
import SpaceBetween from '@cloudscape-design/components/space-between'
import StatusIndicator from '@cloudscape-design/components/status-indicator'
import Table from '@cloudscape-design/components/table'
import { type ValidationError } from '../api/client'

interface ValidationResultsProps {
  valid: boolean
  errors: ValidationError[]
}

const COLUMN_DEFINITIONS = [
  {
    id: 'message',
    header: 'Message',
    cell: (e: ValidationError) => e.message,
    width: '60%',
  },
  {
    id: 'path',
    header: 'Path',
    cell: (e: ValidationError) => e.path ?? '—',
  },
  {
    id: 'line',
    header: 'Line',
    cell: (e: ValidationError) => (e.line != null ? String(e.line) : '—'),
  },
]

export default function ValidationResults({ valid, errors }: ValidationResultsProps) {
  if (valid) {
    return <StatusIndicator type="success">Valid payload</StatusIndicator>
  }

  return (
    <SpaceBetween size="s">
      <StatusIndicator type="error">
        {errors.length} error{errors.length !== 1 ? 's' : ''} found
      </StatusIndicator>
      <Table
        columnDefinitions={COLUMN_DEFINITIONS}
        items={errors}
        empty={<Box textAlign="center" color="inherit">No errors</Box>}
        variant="embedded"
      />
    </SpaceBetween>
  )
}
