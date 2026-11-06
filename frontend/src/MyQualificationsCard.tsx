import { Badge, Group, Paper, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { IconCertificate } from '@tabler/icons-react'
import { formatDate, useT } from '@hubra/plugin-sdk'
import { myQualifications } from './api'
import { STATE_COLOR } from './QualificationsScreen'

/** The member's own qualifications and until when they hold. */
export function MyQualificationsCard() {
  const { t } = useT()
  const { data = [] } = useQuery({ queryKey: ['guides', 'qualifications', 'mine'], queryFn: myQualifications })
  if (data.length === 0) return null
  return (
    <Paper withBorder shadow="sm" radius="lg">
      <Group p="md" gap="sm" style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
        <IconCertificate size={16} style={{ color: '#6b7480' }} />
        <Text fw={700} fz="md">
          {t('qualifications.mine')}
        </Text>
      </Group>
      {data.map((q) => (
        <Group key={q.id} justify="space-between" px="md" py="sm" wrap="nowrap" style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
          <div>
            <Text fw={600} fz="sm">
              {q.kindName}
            </Text>
            <Text fz="xs" c="dimmed">
              {q.expiresOn ? t('qualifications.until', { date: formatDate(q.expiresOn) }) : t('qualifications.noExpiry')}
            </Text>
          </div>
          <Badge variant="light" color={STATE_COLOR[q.state]} style={{ textTransform: 'none', flexShrink: 0 }}>
            {t(`qualifications.state.${q.state}`)}
          </Badge>
        </Group>
      ))}
    </Paper>
  )
}
