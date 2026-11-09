import { registerPlugin } from '@hubra/plugin-sdk'
import { IconBook2 } from '@tabler/icons-react'
import { GuidePage } from './GuidePage'
import { GuideSection } from './GuideSection'
import { GuidesScreen } from './GuidesScreen'
import { ItemGuide } from './ItemGuide'
import translations from './translations.json'

const MODULE = 'guides'
const READ = 'guides.guides.read'

registerPlugin({
  id: 'guides',
  routes: [
    { path: 'guides', module: MODULE, perm: READ, component: GuidesScreen },
    { path: 'guides/:id', module: MODULE, perm: READ, component: GuidePage },
    // Where an item's guide was up to Guides 1.x.
    { path: 'inventory/:id/guide', module: MODULE, perm: READ, component: ItemGuide },
  ],
  slots: [{ slot: 'inventory.item', module: MODULE, component: GuideSection }],
  // The nav entry in hubra_guides/__init__.py names this icon.
  icons: { book: IconBook2 },
  translations,
})
