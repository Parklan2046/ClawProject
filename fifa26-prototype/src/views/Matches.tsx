import { Box, Typography, Card, CardContent, Chip, Grid } from '@mui/material'
import { matches, teams } from '../data/mock'

export default function Matches() {
  const getTeam = (id: number) => teams.find(t => t.id === id)

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 800 }}>Matches</Typography>
      
      <Grid container spacing={2}>
        {matches.map(m => {
          const home = getTeam(m.homeTeamId)
          const away = getTeam(m.awayTeamId)
          return (
            <Grid item xs={12} md={4} key={m.id}>
              <Card sx={{ border: m.status === 'live' ? '1px solid #EF4444' : undefined }}>
                <CardContent>
                  <Chip 
                    label={m.status.toUpperCase()} 
                    color={m.status === 'live' ? 'error' : m.status === 'finished' ? 'default' : 'primary'}
                    size="small" 
                    sx={{ mb: 2 }}
                  />
                  <Typography variant="h6">{home?.flag} {home?.name} vs {away?.flag} {away?.name}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{m.venue}</Typography>
                  
                  {m.status === 'live' && (
                    <Typography variant="h5" sx={{ mt: 2, color: '#00E5FF' }}>
                      {m.homeScore} — {m.awayScore} <span style={{ fontSize: 14 }}>({m.minute}')</span>
                    </Typography>
                  )}
                  {m.status === 'finished' && (
                    <Typography variant="h5" sx={{ mt: 2 }}>{m.homeScore} — {m.awayScore}</Typography>
                  )}
                  {m.status === 'upcoming' && (
                    <Typography variant="body1" sx={{ mt: 2 }}>{new Date(m.date).toLocaleString()}</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </Box>
  )
}
