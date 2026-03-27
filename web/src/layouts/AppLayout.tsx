import { type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import CloudscapeAppLayout from '@cloudscape-design/components/app-layout'
import SideNavigation, { type SideNavigationProps } from '@cloudscape-design/components/side-navigation'

const NAV_ITEMS: SideNavigationProps.Item[] = [
  { type: 'link', text: 'Validate', href: '/validate' },
  { type: 'link', text: 'Probe', href: '/probe' },
  { type: 'link', text: 'Examples', href: '/examples' },
]

export default function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <CloudscapeAppLayout
      navigation={
        <SideNavigation
          header={{ text: 'scim-sanity', href: '/validate' }}
          activeHref={location.pathname}
          items={NAV_ITEMS}
          onFollow={(e) => {
            e.preventDefault()
            navigate(e.detail.href)
          }}
        />
      }
      content={children}
      toolsHide
    />
  )
}
