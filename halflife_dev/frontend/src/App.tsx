import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import RequireAuth from './components/RequireAuth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Home from './pages/Home'
import Library from './pages/Library'
import ItemDetail from './pages/ItemDetail'
import Revisit from './pages/Revisit'
import Insights from './pages/Insights'
import Collections from './pages/Collections'
import CollectionDetail from './pages/CollectionDetail'
import Preferences from './pages/Preferences'
import TestPrompts from './pages/TestPrompts'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<RequireAuth><Layout /></RequireAuth>}>
              <Route path="/" element={<Home />} />
              <Route path="/library" element={<Library />} />
              <Route path="/items/:itemId" element={<ItemDetail />} />
              <Route path="/revisit" element={<Revisit />} />
              <Route path="/insights" element={<Insights />} />
              <Route path="/collections" element={<Collections />} />
              <Route path="/collections/:collectionId" element={<CollectionDetail />} />
              <Route path="/preferences" element={<Preferences />} />
              <Route path="/test-prompts" element={<TestPrompts />} />
            </Route>
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
