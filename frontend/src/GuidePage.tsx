import { useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react'
import {
  Anchor,
  Button,
  Collapse,
  Paper,
  SegmentedControl,
  Select,
  Skeleton,
  Text,
  Textarea,
  TextInput,
  UnstyledButton,
} from '@mantine/core'
import { useDebouncedValue, useMediaQuery } from '@mantine/hooks'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  IconArrowLeft,
  IconCertificate,
  IconChevronDown,
  IconExternalLink,
  IconListDetails,
  IconPackage,
  IconPencil,
  IconTrash,
} from '@tabler/icons-react'
import { ConfirmModal, MarkdownRenderer, PageHead, useAuth, useT, useToast } from '@hubra/plugin-sdk'
import {
  createGuide,
  deleteGuide,
  getGuide,
  pickItems,
  qualificationKinds,
  updateGuide,
  type Guide,
  type GuideInput,
} from './api'
import { headings, readingMinutes, type TocEntry } from './toc'

/** Puts the anchors from `toc` on the rendered h1–h3 headings, in order. */
function useHeadingIds(ref: RefObject<HTMLElement | null>, toc: TocEntry[]) {
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.querySelectorAll('h1, h2, h3').forEach((h, i) => {
      if (!toc[i]) return
      h.id = toc[i].id
      ;(h as HTMLElement).style.scrollMarginTop = '16px'
    })
  })
}

/** The heading the reader is at: the last one above the top third of the window. */
function useActiveHeading(toc: TocEntry[]) {
  const [active, setActive] = useState<string | null>(toc[0]?.id ?? null)
  useEffect(() => {
    if (!toc.length) return
    const onScroll = () => {
      let current = toc[0].id
      for (const entry of toc) {
        const h = document.getElementById(entry.id)
        if (h && h.getBoundingClientRect().top < window.innerHeight / 3) current = entry.id
      }
      setActive(current)
    }
    onScroll()
    // The app scrolls inside its main pane, not the window: listen to both.
    document.addEventListener('scroll', onScroll, { capture: true, passive: true })
    return () => document.removeEventListener('scroll', onScroll, { capture: true })
  }, [toc])
  return active
}

function TocList({
  toc,
  active,
  onPick,
}: {
  toc: TocEntry[]
  active: string | null
  onPick: (id: string) => void
}) {
  return (
    <nav>
      {toc.map((entry) => {
        const on = entry.id === active
        return (
          <a
            key={entry.id}
            href={`#${entry.id}`}
            onClick={(e) => {
              e.preventDefault()
              onPick(entry.id)
            }}
            aria-current={on ? 'location' : undefined}
            style={{
              display: 'block',
              padding: '5px 10px',
              paddingLeft: entry.level === 3 ? 24 : 10,
              borderLeft: `2px solid ${on ? 'var(--mantine-primary-color-filled)' : 'var(--hb-border)'}`,
              color: on ? 'var(--mantine-primary-color-text)' : 'var(--hb-text-2)',
              fontWeight: on ? 600 : 400,
              fontSize: 'var(--mantine-font-size-sm)',
              lineHeight: 1.4,
              textDecoration: 'none',
            }}
          >
            {entry.text}
          </a>
        )
      })}
    </nav>
  )
}

function SideLabel({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        fontSize: 'var(--mantine-font-size-xs)',
        fontWeight: 600,
        color: 'var(--hb-text-3)',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  )
}

function BackToGuides() {
  const { t } = useT()
  return (
    <Button
      component={Link}
      to="/app/guides"
      variant="subtle"
      size="compact-sm"
      leftSection={<IconArrowLeft size={16} />}
      style={{ marginLeft: -8 }}
    >
      {t('guides.back', 'All guides')}
    </Button>
  )
}

/**
 * Writing a guide: title, the item it belongs to (optional), the text with
 * a preview, a link to a manual or video, and the qualification it takes.
 * `guide` is the one being changed; without it a new one is made.
 */
function GuideEditor({ guide, itemId }: { guide?: Guide; itemId?: number }) {
  const { t } = useT()
  const { notify } = useToast()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [title, setTitle] = useState(guide?.title ?? '')
  const [text, setText] = useState(guide?.guide ?? '')
  const [url, setUrl] = useState(guide?.guideUrl ?? '')
  const [item, setItem] = useState<string | null>(
    guide?.itemId ? String(guide.itemId) : itemId ? String(itemId) : null,
  )
  const [qualificationId, setQualificationId] = useState<string | null>(
    guide?.qualification ? String(guide.qualification.id) : null,
  )
  const [mode, setMode] = useState<'write' | 'preview'>('write')
  const [busy, setBusy] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [itemSearch, setItemSearch] = useState('')
  const [itemQuery] = useDebouncedValue(itemSearch.trim(), 250)
  const items = useQuery({ queryKey: ['guides', 'items', itemQuery], queryFn: () => pickItems(itemQuery) })
  const kinds = useQuery({ queryKey: ['guides', 'qualification-kinds'], queryFn: qualificationKinds })
  const rendered = useMemo(() => <MarkdownRenderer content={text} />, [text])

  // The item it has now stays a choice even when the search doesn't find it.
  const itemData = useMemo(() => {
    const rows = (items.data ?? []).map((i) => ({ value: String(i.id), label: i.name }))
    if (guide?.itemId && guide.itemName && !rows.some((r) => r.value === String(guide.itemId))) {
      rows.unshift({ value: String(guide.itemId), label: guide.itemName })
    }
    return rows
  }, [items.data, guide])
  const hasItems = itemData.length > 0 || !!itemQuery
  const hasKinds = (kinds.data?.length ?? 0) > 0

  const done = (id?: number) => {
    if (id) navigate(`/app/guides/${id}`, { replace: true })
    else navigate('/app/guides')
  }

  const save = async () => {
    setBusy(true)
    const input: GuideInput = {
      title: title.trim(),
      guide: text.trim() ? text : null,
      guideUrl: url.trim() || null,
      itemId: item ? Number(item) : null,
    }
    // Without Qualifications the choice isn't shown: keep what is stored.
    if (hasKinds) input.qualificationId = qualificationId ? Number(qualificationId) : null
    try {
      const saved = guide ? await updateGuide(guide.id, input) : await createGuide(input)
      await queryClient.invalidateQueries({ queryKey: ['guides'] })
      notify('success', t('guides.saved', 'Guide saved'))
      done(saved.id)
    } catch (err: unknown) {
      notify('error', t('guides.failed', 'Could not save'), err instanceof Error ? err.message : t('common.unknownError'))
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    if (!guide) return
    await deleteGuide(guide.id)
    await queryClient.invalidateQueries({ queryKey: ['guides'] })
    notify('success', t('guides.deleted', 'Guide deleted'))
    done()
  }

  return (
    <div>
      <PageHead
        back={<BackToGuides />}
        eyebrow={t('guides.guide', 'Guide')}
        title={guide ? guide.title : t('guides.add', 'Add guide')}
        actions={
          guide && (
            <Button variant="default" color="red" leftSection={<IconTrash size={16} />} onClick={() => setDeleting(true)}>
              {t('common.delete', 'Delete')}
            </Button>
          )
        }
      />
      <Paper withBorder p={{ base: 'md', sm: 'xl' }} style={{ maxWidth: 880 }}>
        <TextInput
          required
          value={title}
          onChange={(e) => setTitle(e.currentTarget.value)}
          label={t('guides.titleLabel', 'Title')}
          placeholder={t('guides.titlePlaceholder', 'Laser cutter, Lock up the clubhouse …')}
          maxLength={200}
          mb="md"
        />
        {hasItems && (
          <Select
            mb="md"
            clearable
            searchable
            value={item}
            onChange={setItem}
            searchValue={itemSearch}
            onSearchChange={setItemSearch}
            data={itemData}
            filter={({ options }) => options}
            leftSection={<IconPackage size={16} />}
            label={t('guides.item', 'For the item')}
            description={t('guides.itemHint', 'Shown on that item. Leave empty for a guide on its own.')}
            placeholder={t('guides.noItem', 'No item')}
          />
        )}
        <SegmentedControl
          value={mode}
          onChange={(v) => setMode(v as 'write' | 'preview')}
          data={[
            { value: 'write', label: t('guides.write', 'Write') },
            { value: 'preview', label: t('guides.preview', 'Preview') },
          ]}
          mb="md"
        />
        {mode === 'write' ? (
          <Textarea
            aria-label={t('guides.guide', 'Guide')}
            placeholder={t('guides.placeholder', 'Steps, safety rules, what to check after use. Markdown works.')}
            description={t(
              'guides.headingsHint',
              'Start a section with ## Heading: it gets its own entry in the table of contents and a link of its own.',
            )}
            value={text}
            onChange={(e) => setText(e.currentTarget.value)}
            autosize
            minRows={14}
            maxRows={40}
            styles={{ input: { fontFamily: 'var(--mantine-font-family-monospace)', fontSize: 14, lineHeight: 1.6 } }}
          />
        ) : (
          <div
            style={{
              minHeight: 200,
              padding: 16,
              border: '1px solid var(--hb-border)',
              borderRadius: 'var(--mantine-radius-md)',
              lineHeight: 1.7,
            }}
          >
            {text.trim() ? rendered : <Text c="dimmed">{t('guides.previewEmpty', 'Nothing to preview yet.')}</Text>}
          </div>
        )}
        <TextInput
          mt="lg"
          value={url}
          onChange={(e) => setUrl(e.currentTarget.value)}
          label={t('guides.link', 'Link to manual or video')}
          placeholder="https://"
        />
        {hasKinds && (
          <Select
            mt="md"
            clearable
            value={qualificationId}
            onChange={setQualificationId}
            data={(kinds.data ?? []).map((k) => ({ value: String(k.id), label: k.name }))}
            label={t('guides.qualification.needed', 'Qualification it takes')}
            description={t('guides.qualification.neededHint', 'Shown with the guide, with whether the reader holds it.')}
            placeholder={t('guides.qualification.noneNeeded', 'None')}
          />
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 24 }}>
          <Button variant="subtle" onClick={() => (guide ? done(guide.id) : navigate(-1))}>
            {t('common.cancel')}
          </Button>
          <Button onClick={save} loading={busy} disabled={!title.trim()}>
            {t('common.save')}
          </Button>
        </div>
      </Paper>
      <ConfirmModal
        open={deleting}
        onClose={() => setDeleting(false)}
        title={t('guides.deleteTitle', 'Delete «{{name}}»?', { name: guide?.title ?? '' })}
        body={t('guides.deleteBody', 'The guide is deleted for good.')}
        onConfirm={remove}
      />
    </div>
  )
}

/**
 * A guide as a page of its own, /app/guides/<id>: the guide at reading
 * width, a table of contents beside it (above it on phones). `?edit=1`
 * opens the editor; /app/guides/new?item=<id> writes a new one for an item;
 * `#<heading>` links to a section.
 */
export function GuidePage() {
  const { t } = useT()
  const { hasPermission } = useAuth()
  const { hash } = useLocation()
  const [params, setParams] = useSearchParams()
  const raw = useParams().id
  const isNew = raw === 'new'
  const guideId = Number(raw)
  const canWrite = hasPermission('guides.guides.write')
  const wide = useMediaQuery('(min-width: 62em)', true)

  const { data: guide, isLoading, error } = useQuery({
    queryKey: ['guides', guideId],
    queryFn: () => getGuide(guideId),
    enabled: !isNew && Number.isFinite(guideId),
  })

  const editing = canWrite && params.get('edit') === '1'
  const [tocOpen, setTocOpen] = useState(false)

  const content = guide?.guide ?? ''
  const toc = useMemo(() => headings(content), [content])
  const articleRef = useRef<HTMLDivElement>(null)
  // The same element on every render, so the headings are not remounted
  // (and lose their ids) when the active heading changes.
  const rendered = useMemo(() => <MarkdownRenderer content={content} />, [content])
  useHeadingIds(articleRef, toc)
  const active = useActiveHeading(editing ? [] : toc)

  const jump = (id: string, smooth = true) => {
    const el = document.getElementById(id)
    if (!el) return
    el.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' })
    window.history.replaceState(window.history.state, '', `#${id}`)
    setTocOpen(false)
  }

  // A link to a section (#vor-dem-einschalten) scrolls there once the guide is in.
  useEffect(() => {
    if (!hash || !toc.length || editing) return
    const id = decodeURIComponent(hash.slice(1))
    const timer = window.setTimeout(() => jump(id, false), 50)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hash, toc, editing])

  if (isNew) {
    const item = Number(params.get('item'))
    return canWrite ? <GuideEditor itemId={Number.isFinite(item) && item > 0 ? item : undefined} /> : null
  }

  if (isLoading) {
    return (
      <div>
        <Skeleton height={20} width={160} mb={16} />
        <Skeleton height={36} width={320} mb={24} />
        <Skeleton height={280} />
      </div>
    )
  }

  if (error || !guide) {
    return (
      <div>
        <PageHead
          title={t('guides.notFound', 'Guide not found')}
          desc={t('guides.notFoundDesc', 'It may have been deleted.')}
          back={<BackToGuides />}
        />
      </div>
    )
  }

  if (editing) return <GuideEditor key={guide.id} guide={guide} />

  const setEditing = () => {
    const next = new URLSearchParams(params)
    next.set('edit', '1')
    setParams(next, { replace: true })
  }
  const itemPath = guide.itemId ? `/app/inventory/${guide.itemId}` : null
  const minutes = readingMinutes(content)
  const meta = [
    toc.length ? t('guides.sections', '{{count}} sections', { count: toc.length }) : null,
    content ? t('guides.minutes', '{{count}} min read', { count: minutes }) : null,
  ]
    .filter(Boolean)
    .join(' · ')

  const manualButton = guide.guideUrl && (
    <Button
      component="a"
      href={guide.guideUrl}
      target="_blank"
      rel="noopener noreferrer"
      variant="default"
      leftSection={<IconExternalLink size={16} />}
    >
      {t('guides.openLink', 'Open manual')}
    </Button>
  )

  const head = (
    <PageHead
      back={<BackToGuides />}
      eyebrow={guide.itemName ?? t('guides.guide', 'Guide')}
      title={guide.title}
      desc={meta || undefined}
      actions={
        <>
          {content && manualButton}
          {canWrite && (
            <Button variant="default" leftSection={<IconPencil size={16} />} onClick={setEditing}>
              {t('common.edit', 'Edit')}
            </Button>
          )}
        </>
      }
    />
  )

  const note = (icon: ReactNode, children: ReactNode, warn = false) => (
    <div
      style={{
        display: 'flex',
        gap: 8,
        alignItems: 'flex-start',
        fontSize: 'var(--mantine-font-size-sm)',
        color: warn ? 'var(--mantine-color-red-7)' : 'var(--hb-text-2)',
        lineHeight: 1.45,
      }}
    >
      {icon}
      <span>{children}</span>
    </div>
  )
  const itemNote =
    itemPath &&
    note(
      <IconPackage size={16} style={{ flexShrink: 0, marginTop: 2 }} />,
      <>
        {guide.instructionRequired
          ? t('guides.needsInstruction', 'This item needs an induction before first use.')
          : t('guides.forItem', 'For the item')}{' '}
        <Anchor component={Link} to={itemPath} fz="sm">
          {guide.instructionRequired ? t('guides.seeItem', 'See who is inducted') : guide.itemName}
        </Anchor>
      </>,
    )
  const q = guide.qualification
  const qualificationNote =
    q &&
    note(
      <IconCertificate size={16} style={{ flexShrink: 0, marginTop: 2 }} />,
      <>
        {t('guides.qualification.takes', 'It takes: {{name}}.', { name: q.name })}{' '}
        {t(`guides.qualification.yours.${q.mine ?? 'none'}`)}
      </>,
      q.mine !== 'valid',
    )

  const article = (
    <Paper withBorder p={{ base: 'md', sm: 'xl' }} style={{ minWidth: 0 }}>
      {content ? (
        <div ref={articleRef} style={{ lineHeight: 1.7, maxWidth: 720 }}>
          {rendered}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '32px 8px' }}>
          <Text c="dimmed" fz="sm" mb={canWrite ? 'md' : 0}>
            {guide.guideUrl
              ? t('guides.onlyLink', 'This guide is a link to the manual.')
              : t('guides.empty', 'This guide has no text yet.')}
          </Text>
          {guide.guideUrl && <div style={{ marginTop: 12 }}>{manualButton}</div>}
          {canWrite && !guide.guideUrl && (
            <Button variant="default" onClick={setEditing}>
              {t('common.edit', 'Edit')}
            </Button>
          )}
        </div>
      )}
    </Paper>
  )

  if (!wide) {
    return (
      <div>
        {head}
        {itemNote && <div style={{ marginBottom: 16 }}>{itemNote}</div>}
        {qualificationNote && <div style={{ marginBottom: 16 }}>{qualificationNote}</div>}
        {toc.length > 1 && (
          <Paper withBorder mb="md" style={{ overflow: 'hidden' }}>
            <UnstyledButton
              onClick={() => setTocOpen((o) => !o)}
              aria-expanded={tocOpen}
              style={{
                display: 'flex',
                width: '100%',
                alignItems: 'center',
                gap: 10,
                padding: '12px 16px',
                fontSize: 'var(--mantine-font-size-sm)',
                fontWeight: 600,
                color: 'var(--hb-text)',
              }}
            >
              <IconListDetails size={18} />
              <span style={{ flex: 1 }}>
                {t('guides.contents', 'Contents')}
                <span style={{ fontWeight: 400, color: 'var(--hb-text-3)' }}> · {toc.length}</span>
              </span>
              <IconChevronDown
                size={18}
                style={{ transform: tocOpen ? 'rotate(180deg)' : undefined, transition: 'transform 150ms' }}
              />
            </UnstyledButton>
            <Collapse expanded={tocOpen}>
              <div style={{ padding: '0 16px 14px' }}>
                <TocList toc={toc} active={active} onPick={jump} />
              </div>
            </Collapse>
          </Paper>
        )}
        {article}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      {head}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) 260px',
          gap: 32,
          alignItems: 'start',
        }}
      >
        {article}
        <aside style={{ position: 'sticky', top: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>
          {toc.length > 1 && (
            <div>
              <SideLabel>{t('guides.contents', 'Contents')}</SideLabel>
              <TocList toc={toc} active={active} onPick={jump} />
            </div>
          )}
          {itemNote}
          {qualificationNote}
        </aside>
      </div>
    </div>
  )
}
