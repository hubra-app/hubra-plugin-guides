import { apiFetch } from '@hubra/plugin-sdk'

/** Whether the reader holds the qualification a guide takes. */
export type QualificationState = 'valid' | 'soon' | 'expired'

/** A guide in the list. */
export interface GuideSummary {
  id: number
  title: string
  itemId: number | null
  itemName: string | null
  /** The first line of text. */
  preview: string
  hasText: boolean
  guideUrl: string | null
  updatedAt: string | null
}

export interface Guide extends GuideSummary {
  guide: string
  instructionRequired: boolean
  /** The qualification it takes (Qualifications plugin), and whether I hold it. */
  qualification: { id: number; name: string; mine: QualificationState | null } | null
}

export interface GuideInput {
  title: string
  guide: string | null
  guideUrl: string | null
  itemId: number | null
  /** Left out when the Qualifications plugin is not there: keeps what is stored. */
  qualificationId?: number | null
}

export interface Choice {
  id: number
  name: string
}

const G = '/guides'

export const listGuides = (params: { q?: string; itemId?: number } = {}) => {
  const query = new URLSearchParams()
  if (params.q) query.set('q', params.q)
  if (params.itemId !== undefined) query.set('itemId', String(params.itemId))
  return apiFetch<GuideSummary[]>(`${G}/?${query}`)
}
export const getGuide = (id: number) => apiFetch<Guide>(`${G}/${id}`)
export const createGuide = (input: GuideInput) =>
  apiFetch<Guide>(`${G}/`, { method: 'POST', body: JSON.stringify(input) })
export const updateGuide = (id: number, input: Partial<GuideInput>) =>
  apiFetch<Guide>(`${G}/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteGuide = (id: number) => apiFetch<void>(`${G}/${id}`, { method: 'DELETE' })
/** Inventory items to pick from (empty without Inventory). */
export const pickItems = (q: string) => apiFetch<Choice[]>(`${G}/items?${new URLSearchParams({ q })}`)
/** Qualifications a guide can name (empty without Qualifications). */
export const qualificationKinds = () => apiFetch<Choice[]>(`${G}/qualification-kinds`)
