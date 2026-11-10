import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge, Button, Group, Paper, SimpleGrid, Stack, Text, TextInput, UnstyledButton } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { IconBook2, IconExternalLink, IconPackage, IconPlus, IconSearch } from '@tabler/icons-react'
import { EmptyState, ErrorBanner, LoadingSpinner, PageHead, useAuth, useNav, useT } from '@hubra/plugin-sdk'
import { listGuides } from './api'

/** Every guide, searchable: how-tos for items and for anything else. */
export function GuidesScreen() {
  const { t } = useT()
  const { go } = useNav()
  const { hasPermission } = useAuth()
  const canWrite = hasPermission('guides.guides.write')
  const [q, setQ] = useState('')
  const [search] = useDebouncedValue(q.trim(), 250)
  const list = useQuery({ queryKey: ['guides', 'list', search], queryFn: () => listGuides({ q: search }) })

  return (
    <>
      <PageHead
        title={t('guides.title', 'Guides')}
        desc={t('guides.desc', 'How-tos for machines, tools and everything else in the club.')}
        actions={
          canWrite && (
            <Button leftSection={<IconPlus size={16} />} onClick={() => go('/app/guides/new')}>
              {t('guides.add', 'Add guide')}
            </Button>
          )
        }
      />
      <TextInput
        leftSection={<IconSearch size={16} />}
        placeholder={t('guides.search', 'Search guides')}
        value={q}
        onChange={(e) => setQ(e.currentTarget.value)}
        mb="md"
        maw={360}
      />
      {list.error ? (
        <ErrorBanner message={(list.error as Error).message} onRetry={() => list.refetch()} />
      ) : list.isLoading ? (
        <LoadingSpinner />
      ) : !list.data?.length ? (
        <EmptyState
          icon={<IconBook2 size={28} />}
          title={search ? t('guides.noMatch', 'No guide matches.') : t('guides.none', 'No guides yet.')}
          description={search ? undefined : t('guides.noneHint', 'Write down how a machine works or how something is done in the club.')}
        />
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="sm">
          {list.data.map((g) => (
            <UnstyledButton key={g.id} onClick={() => go(`/app/guides/${g.id}`)} style={{ display: 'block' }}>
              <Paper withBorder radius="md" p="md" style={{ height: '100%' }}>
                <Stack gap={6}>
                  <Group gap={8} wrap="nowrap">
                    <IconBook2 size={18} style={{ flexShrink: 0, color: 'var(--hb-text-3)' }} />
                    <Text fw={700} truncate>
                      {g.title}
                    </Text>
                  </Group>
                  {g.preview && (
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {g.preview}
                    </Text>
                  )}
                  <Group gap={6}>
                    {g.itemName && (
                      <Badge variant="light" color="gray" leftSection={<IconPackage size={12} />} style={{ textTransform: 'none' }}>
                        {g.itemName}
                      </Badge>
                    )}
                    {g.guideUrl && (
                      <Badge variant="light" color="gray" leftSection={<IconExternalLink size={12} />} style={{ textTransform: 'none' }}>
                        {t('guides.hasLink', 'Manual')}
                      </Badge>
                    )}
                  </Group>
                </Stack>
              </Paper>
            </UnstyledButton>
          ))}
        </SimpleGrid>
      )}
    </>
  )
}
