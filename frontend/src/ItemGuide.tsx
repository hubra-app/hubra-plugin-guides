import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { LoadingSpinner, useAuth } from '@hubra/plugin-sdk'
import { listGuides } from './api'

/**
 * /app/inventory/<id>/guide, where an item's guide was up to Guides 1.x:
 * opens the item's guide, or writes one when it has none.
 */
export function ItemGuide() {
  const itemId = Number(useParams().id)
  const navigate = useNavigate()
  const { hasPermission } = useAuth()
  const { data } = useQuery({
    queryKey: ['guides', 'list', 'item', itemId],
    queryFn: () => listGuides({ itemId }),
    enabled: Number.isFinite(itemId),
  })
  useEffect(() => {
    if (!data) return
    if (data.length) navigate(`/app/guides/${data[0].id}`, { replace: true })
    else if (hasPermission('guides.guides.write')) navigate(`/app/guides/new?item=${itemId}`, { replace: true })
    else navigate(`/app/inventory/${itemId}`, { replace: true })
  }, [data, itemId, navigate, hasPermission])
  return <LoadingSpinner />
}
