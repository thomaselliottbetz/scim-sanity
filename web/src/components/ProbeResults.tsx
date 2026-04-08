import Alert from '@cloudscape-design/components/alert'
import Box from '@cloudscape-design/components/box'
import ExpandableSection from '@cloudscape-design/components/expandable-section'
import SpaceBetween from '@cloudscape-design/components/space-between'
import StatusIndicator, { type StatusIndicatorProps } from '@cloudscape-design/components/status-indicator'
import Table from '@cloudscape-design/components/table'
import { type ProbeIssue, type ProbeResponse, type ProbeTestResult } from '../api/client'

// Maps probe status strings to Cloudscape StatusIndicator types
const STATUS_TYPE: Record<string, StatusIndicatorProps.Type> = {
  pass: 'success',
  fail: 'error',
  warn: 'warning',
  skip: 'stopped',
  error: 'error',
}

const RESULT_COLUMNS = [
  {
    id: 'status',
    header: 'Status',
    width: 110,
    cell: (r: ProbeTestResult) => (
      <StatusIndicator type={STATUS_TYPE[r.status] ?? 'info'}>
        {r.status.toUpperCase()}
      </StatusIndicator>
    ),
  },
  {
    id: 'name',
    header: 'Test',
    cell: (r: ProbeTestResult) => r.name,
  },
  {
    id: 'message',
    header: 'Detail',
    cell: (r: ProbeTestResult) => r.message ?? '',
  },
]

function groupByPhase(results: ProbeTestResult[]): Map<string, ProbeTestResult[]> {
  const phases = new Map<string, ProbeTestResult[]>()
  for (const r of results) {
    const phase = r.phase ?? 'Other'
    if (!phases.has(phase)) phases.set(phase, [])
    phases.get(phase)!.push(r)
  }
  return phases
}

function SummaryBar({ summary, mode, timestamp }: Pick<ProbeResponse, 'summary' | 'mode' | 'timestamp'>) {
  return (
    <SpaceBetween size="l" direction="horizontal">
      <StatusIndicator type="success">{summary.passed} passed</StatusIndicator>
      <StatusIndicator type={summary.failed > 0 ? 'error' : 'success'}>
        {summary.failed} failed
      </StatusIndicator>
      <StatusIndicator type={summary.errors > 0 ? 'error' : 'success'}>
        {summary.errors} errors
      </StatusIndicator>
      <StatusIndicator type={summary.warnings > 0 ? 'warning' : 'success'}>
        {summary.warnings} warnings
      </StatusIndicator>
      <StatusIndicator type="stopped">{summary.skipped} skipped</StatusIndicator>
      <Box variant="small" color="text-status-inactive">
        {summary.total} total · {mode} mode · {timestamp}
      </Box>
    </SpaceBetween>
  )
}

function FixSummary({ issues }: { issues: ProbeIssue[] }) {
  return (
    <Alert type="warning" header="Fix Summary">
      <SpaceBetween size="m">
        {issues.map((issue) => (
          <SpaceBetween key={issue.title} size="xxs">
            <Box variant="p">
              <strong>[{issue.priority}] Trouble:</strong> {issue.title}
              {' '}
              <Box variant="span" color="text-status-inactive">
                ({issue.affected_tests} test{issue.affected_tests !== 1 ? 's' : ''} affected)
              </Box>
            </Box>
            <Box variant="p"><strong>Fix:</strong> {issue.fix}</Box>
            <Box variant="p"><strong>Rationale:</strong> <Box variant="span" color="text-status-inactive">{issue.rationale}</Box></Box>
          </SpaceBetween>
        ))}
      </SpaceBetween>
    </Alert>
  )
}

interface ProbeResultsProps {
  result: ProbeResponse
}

export default function ProbeResults({ result }: ProbeResultsProps) {
  const phases = groupByPhase(result.results)
  const hasFailures = result.summary.failed > 0 || result.summary.errors > 0

  return (
    <SpaceBetween size="l">
      <SummaryBar
        summary={result.summary}
        mode={result.mode}
        timestamp={result.timestamp}
      />

      {Array.from(phases.entries()).map(([phase, tests]) => {
        const failCount = tests.filter((t) => t.status === 'fail' || t.status === 'error').length
        const warnCount = tests.filter((t) => t.status === 'warn').length
        const headerSuffix = failCount > 0
          ? ` — ${failCount} failure${failCount !== 1 ? 's' : ''}`
          : warnCount > 0
          ? ` — ${warnCount} warning${warnCount !== 1 ? 's' : ''}`
          : ''

        return (
          <ExpandableSection
            key={phase}
            headerText={phase + headerSuffix}
            defaultExpanded={failCount > 0 || warnCount > 0}
            variant="container"
          >
            <Table
              columnDefinitions={RESULT_COLUMNS}
              items={tests}
              variant="embedded"
              empty={<Box textAlign="center" color="inherit">No results</Box>}
            />
          </ExpandableSection>
        )
      })}

      {hasFailures && result.issues.length > 0 && (
        <FixSummary issues={result.issues} />
      )}
    </SpaceBetween>
  )
}
