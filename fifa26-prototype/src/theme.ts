import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#0A1428',
      paper: '#121C35'
    },
    primary: {
      main: '#00E5FF',
      contrastText: '#0A1428'
    },
    secondary: {
      main: '#FFD700',
      contrastText: '#0A1428'
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#A0AEC0'
    },
    success: { main: '#22C55E' },
    error: { main: '#EF4444' },
    divider: 'rgba(255,255,255,0.08)'
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 800, fontSize: '2.5rem' },
    h2: { fontWeight: 700, fontSize: '2rem' },
    h3: { fontWeight: 700, fontSize: '1.5rem' },
    h4: { fontWeight: 600, fontSize: '1.25rem' },
    body1: { fontWeight: 400 },
    body2: { fontWeight: 400, color: '#A0AEC0' }
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          background: '#121C35',
          border: '1px solid rgba(255,255,255,0.08)',
          backdropFilter: 'blur(20px)'
        }
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: '#121C35',
          border: '1px solid rgba(255,255,255,0.08)'
        }
      }
    }
  }
})
