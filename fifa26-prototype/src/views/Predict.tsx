import { useState } from 'react'
import { Box, Typography, Card, CardContent, Button, LinearProgress, Grid } from '@mui/material'
import { championPredictions, teams } from '../data/mock'

export default function Predict() {
  const [results, setResults] = useState(championPredictions)
  const [running, setRunning] = useState(false)

  const runSimulation = () => {
    setRunning(true)
    setTimeout(() => {
      // Simulate slight probability shifts
      const shuffled = [...results].sort(() => Math.random() - 0.5)
      setResults(shuffled.map((r, i) => ({ ...r, probability: Math.max(0.05, 0.3 - i * 0.04) })))
      setRunning(false)
    }, 800)
  }

  const top = [...results].sort((a, b) => b.probability - a.probability)[0]
  const topTeam = teams.find(t => t.id === top.teamId)

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 800 }}>AI World Cup Champion Predictor</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Full-round simulation powered by advanced analytics
      </Typography>

      <Button 
        variant="contained" 
        onClick={runSimulation} 
        disabled={running}
        sx={{ mb: 4, bgcolor: '#00E5FF', color: '#0A1428', fontWeight: 700 }}
      >
        {running ? 'Running Simulation...' : 'Run Full Tournament Simulation'}
      </Button>

      {/* Champion Card */}
      <Card sx={{ mb: 4, border: '2px solid #FFD700' }}>
        <CardContent>
          <Typography variant="overline">Most Likely Champion</Typography>
          <Typography variant="h3" sx={{ mt: 1, fontWeight: 800 }}>{topTeam?.flag} {topTeam?.name}</Typography>
          <Typography variant="h2" sx={{ mt: 1, color: '#FFD700' }}>{(top.probability * 100).toFixed(0)}%</Typography>
        </CardContent>
      </Card>

      {/* Probability Bars */}
      <Typography variant="h6" sx={{ mb: 2 }}>Top Contenders</Typography>
      <Grid container spacing={2}>
        {results.sort((a, b) => b.probability - a.probability).map((p, i) => {
          const team = teams.find(t => t.id === p.teamId)
          return (
            <Grid item xs={12} md={6} key={i}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography>{team?.flag} {team?.name}</Typography>
                    <Typography sx={{ color: '#00E5FF' }}>{(p.probability * 100).toFixed(0)}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={p.probability * 100} 
                    sx={{ height: 8, borderRadius: 1, bgcolor: '#1A2744' }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>{p.reason}</Typography>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </Box>
  )
}
