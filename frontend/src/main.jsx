import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, createRoutesFromElements } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import './index.css'
import { appRoutes } from './App.jsx'

const router = createBrowserRouter(createRoutesFromElements(appRoutes))

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
