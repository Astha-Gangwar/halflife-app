import React from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

// Mounted once by App's route tree, wrapping every authenticated page as an
// <Outlet/> child instead of each page rendering its own <Navbar/>. Before
// this, navigating between pages unmounted and remounted the entire layout
// (Navbar included) on every click -- no network reload, but a full visual
// tear-down and rebuild that looked and felt like one.
const Layout: React.FC = () => {
  return (
    <div>
      <Navbar />
      <Outlet />
    </div>
  )
}

export default Layout
