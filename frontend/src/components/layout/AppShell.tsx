import { Outlet } from 'react-router-dom'
import TopNav from './TopNav'
import ChatPanel from './ChatPanel'

export default function AppShell() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <TopNav />
      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-y-auto bg-navy-900">
          <Outlet />
        </main>
        <ChatPanel />
      </div>
    </div>
  )
}
