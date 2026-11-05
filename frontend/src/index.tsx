import { registerPlugin } from '@hubra/plugin-sdk'
import { IconCertificate } from '@tabler/icons-react'
import { GuidePage } from './GuidePage'
import { GuideSection } from './GuideSection'
import { MyQualificationsCard } from './MyQualificationsCard'
import { QualificationsScreen } from './QualificationsScreen'
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
    {
      path: 'inventory/qualifications',
      module: 'inventory.guides',
      perm: 'guides.qualifications.manage',
      component: QualificationsScreen,
    },
  ],
  slots: [
    { slot: 'inventory.item', module: 'inventory.guides', component: GuideSection },
    { slot: 'account.cards', module: 'inventory.guides', component: MyQualificationsCard },
  ],
  // The nav entry in hubra_guides/__init__.py names this icon.
  icons: { certificate: IconCertificate },
  translations,
})
