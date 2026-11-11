import { Button, Text, UnstyledButton } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { IconBook2, IconChevronRight, IconExternalLink, IconPlus } from '@tabler/icons-react'
import { useAuth, useT } from '@hubra/plugin-sdk'
import { itemGuides } from './api'

/**
 * Shown on an inventory item: the guides for it, each opening its own page,
 * and a button to write one.
 */
export function GuideSection({ itemId }: { itemId: number }) {
  const { t } = useT()
  const { hasPermission } = useAuth()
  const canWrite = hasPermission('guides.guides.write')
  const { data: guides } = useQuery({
    queryKey: ['guides', 'list', 'item', itemId],
    queryFn: () => itemGuides(itemId),
  })

  if (!guides || (!guides.length && !canWrite)) return null
  const add = `/app/guides/new?item=${itemId}`

  return (
    <section style={{ padding: '16px 20px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          marginBottom: 10,
        }}
      >
        <div
          style={{
            fontSize: 'var(--mantine-font-size-xs)',
            fontWeight: 600,
            color: 'var(--hb-text-3)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          }}
        >
          {t('guides.title', 'Guides')}
        </div>
        {canWrite && guides.length > 0 && (
          <Button component={Link} to={add} size="compact-xs" variant="subtle" leftSection={<IconPlus size={14} />}>
            {t('guides.addShort', 'Add')}
          </Button>
        )}
      </div>
      {guides.length === 0 ? (
        <Button component={Link} to={add} variant="default" fullWidth leftSection={<IconPlus size={16} />}>
          {t('guides.add', 'Add guide')}
        </Button>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {guides.map((g) => (
            <UnstyledButton
              key={g.id}
              component={Link}
              to={`/app/guides/${g.id}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                border: '1px solid var(--hb-border)',
                borderRadius: 'var(--mantine-radius-md)',
                padding: '10px 12px',
                background: 'var(--hb-surface-2)',
              }}
            >
              {g.hasText || !g.guideUrl ? (
                <IconBook2 size={18} style={{ flexShrink: 0, color: 'var(--hb-text-3)' }} />
              ) : (
                <IconExternalLink size={18} style={{ flexShrink: 0, color: 'var(--hb-text-3)' }} />
              )}
              <div style={{ minWidth: 0, flex: 1 }}>
                <Text fz="sm" fw={600} truncate>
                  {g.title}
                </Text>
                {g.preview && (
                  <Text fz="xs" c="dimmed" truncate>
                    {g.preview}
                  </Text>
                )}
              </div>
              <IconChevronRight size={16} style={{ flexShrink: 0, color: 'var(--hb-text-3)' }} />
            </UnstyledButton>
          ))}
        </div>
      )}
    </section>
  )
}
