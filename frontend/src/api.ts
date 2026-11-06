import { apiFetch } from '@hubra/plugin-sdk'

export interface Guide {
  itemId: number
  itemName: string
  guide: string | null
  guideUrl: string | null
  instructionRequired: boolean
  /** The qualification it takes to use the item, and whether I hold it. */
  qualification: { id: number; name: string; mine: QualificationState | null } | null
}

export type QualificationState = 'valid' | 'soon' | 'expired'

export const getGuide = (itemId: number) => apiFetch<Guide>(`/guides/${itemId}`)

export const saveGuide = (
  itemId: number,
  input: { guide: string | null; guideUrl: string | null; qualificationId: number | null },
) =>
  apiFetch<Guide>(`/guides/${itemId}`, {
    method: 'PUT',
    body: JSON.stringify({
      guide: input.guide,
      guide_url: input.guideUrl,
      qualification_id: input.qualificationId,
    }),
  })

// ── Qualifications ──────────────────────────────────────────────────────────

export interface QualificationKind {
  id: number
  name: string
  description: string | null
  validMonths: number | null
  remindDays: number
}

export interface Qualification {
  id: number
  memberId: number
  memberName: string | null
  kindId: number
  kindName: string
  obtainedOn: string
  expiresOn: string | null
  note: string | null
  state: QualificationState
}

export interface KindInput {
  name: string
  description: string | null
  validMonths: number | null
  remindDays: number
}

export interface QualificationInput {
  memberId?: number
  kindId?: number
  obtainedOn: string
  expiresOn?: string | null
  note: string | null
}

const Q = '/guides/qualifications'
export const listKinds = () => apiFetch<QualificationKind[]>(`${Q}/kinds`)
export const createKind = (input: KindInput) =>
  apiFetch<QualificationKind>(`${Q}/kinds`, { method: 'POST', body: JSON.stringify(input) })
export const updateKind = (id: number, input: KindInput) =>
  apiFetch<QualificationKind>(`${Q}/kinds/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteKind = (id: number) => apiFetch<void>(`${Q}/kinds/${id}`, { method: 'DELETE' })
export const listQualifications = () => apiFetch<Qualification[]>(Q)
export const myQualifications = () => apiFetch<Qualification[]>(`${Q}/mine`)
export const addQualification = (input: QualificationInput) =>
  apiFetch<Qualification>(Q, { method: 'POST', body: JSON.stringify(input) })
export const updateQualification = (id: number, input: QualificationInput) =>
  apiFetch<Qualification>(`${Q}/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteQualification = (id: number) => apiFetch<void>(`${Q}/${id}`, { method: 'DELETE' })
