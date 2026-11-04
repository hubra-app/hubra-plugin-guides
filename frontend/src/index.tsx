import { registerPlugin } from '@hubra/plugin-sdk'
import { GuidePage } from './GuidePage'
import { GuideSection } from './GuideSection'
import translations from './translations.json'

registerPlugin({
  id: 'guides',
  routes: [
    {
      path: 'inventory/:id/guide',
      module: 'inventory.guides',
      perm: 'guides.guides.read',
      component: GuidePage,
    },
  ],
  slots: [{ slot: 'inventory.item', module: 'inventory.guides', component: GuideSection }],
  translations,
})
