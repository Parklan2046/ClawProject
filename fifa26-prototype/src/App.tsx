import { Routes, Route, Link as RouterLink } from 'react-router-dom'
import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material'
import Dashboard from './views/Dashboard'
import Matches from './views/Matches'
import History from './views/History'
import Predict from './views/Predict'

export default function App() {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" sx={{ bgcolor: '#0A1428', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 800, color: '#00E5FF' }}>
            FIFA 26
          </Typography>
          <Button component={RouterLink} to="/" color="inherit">Dashboard</Button>
          <Button component={RouterLink} to="/matches" color="inherit">Matches</Button>
          <Button component={RouterLink} to="/history" color="inherit">History</Button>
          <Button component={RouterLink} to="/predict" color="inherit" sx={{ color: '#FFD700' }}>AI Predictor</Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/matches" element={<Matches />} />
          <Route path="/history" element={<History />} />
          <Route path="/predict" element={<Predict />} />
        </Routes>
      </Container>

      <Box component="footer" sx={{ py: 3, textAlign: 'center', color: 'text.secondary', fontSize: 12 }}>
        FIFA 26 Match Intelligence Hub — Design Portfolio Prototype
      </Box>
    </Box>
  )
}
