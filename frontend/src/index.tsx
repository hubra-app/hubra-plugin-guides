import { registerPlugin } from '@hubra/plugin-sdk'
import { IconCertificate, IconTools } from '@tabler/icons-react'
import { CanDoScreen } from './CanDoScreen'
import { MyQualificationsCard } from './MyQualificationsCard'
import { QualificationsScreen } from './QualificationsScreen'
import translations from './translations.json'

const MODULE = 'qualifications'

// The usage guides per item moved into Inventory (2.4); this plugin keeps
// the qualifications and who can do what.
registerPlugin({
  id: 'guides',
  routes: [
    { path: 'skills', module: MODULE, component: CanDoScreen },
    { path: 'qualifications', module: MODULE, perm: 'guides.qualifications.manage', component: QualificationsScreen },
    // The address it had under Inventory, for old links and reminders.
    { path: 'inventory/qualifications', module: MODULE, perm: 'guides.qualifications.manage', component: QualificationsScreen },
  ],
  slots: [{ slot: 'account.cards', module: MODULE, component: MyQualificationsCard }],
  // The nav entries in hubra_guides/__init__.py name these icons.
  icons: { certificate: IconCertificate, tools: IconTools },
  translations,
})
