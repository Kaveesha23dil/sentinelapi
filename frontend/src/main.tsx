import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import '@fontsource-variable/inter'
import './styles.css'
import { App } from './app'
import { SessionProvider } from './hooks/session'
import { PeriodProvider } from './hooks/period'
import { ErrorBoundary } from './components/common'
const client = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: true } } })
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={client}>
        <BrowserRouter>
          <SessionProvider>
            <PeriodProvider>
              <App />
            </PeriodProvider>
          </SessionProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
