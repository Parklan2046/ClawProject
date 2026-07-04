import { Grid, Typography, Card, CardContent, Box } from '@mui/material'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { matches, goalsPerMatch, cardDistribution, topScorers } from '../data/mock'

export default function Dashboard() {
  const liveMatch = matches.find(m => m.status === 'live')

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 800 }}>Match Intelligence Hub</Typography>
      
      {/* KPI Strip */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[
          { label: 'Matches Played', value: '48' },
          { label: 'Total Goals', value: '142' },
          { label: 'Cards Issued', value: '187' },
          { label: 'Peak Viewers', value: '2.8M' }
        ].map((kpi, i) => (
          <Grid item xs={6} md={3} key={i}>
            <Card>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#00E5FF' }}>{kpi.value}</Typography>
                <Typography variant="body2" color="text.secondary">{kpi.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Live Match */}
      {liveMatch && (
        <Card sx={{ mb: 4, border: '1px solid #00E5FF' }}>
          <CardContent>
            <Typography variant="overline" sx={{ color: '#EF4444' }}>● LIVE</Typography>
            <Typography variant="h5" sx={{ mt: 1 }}>
              France vs Brazil — {liveMatch.minute}'
            </Typography>
            <Typography variant="h4" sx={{ mt: 1, fontWeight: 800 }}>
              {liveMatch.homeScore} — {liveMatch.awayScore}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Season Snapshot Charts */}
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>2026 Season Snapshot</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>Goals per Match</Typography>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={goalsPerMatch}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="goals" stroke="#00E5FF" fill="#00E5FF" fillOpacity={0.2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>Card Distribution</Typography>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={cardDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="stage" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="yellow" fill="#FFD700" />
                  <Bar dataKey="red" fill="#EF4444" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Scorers */}
      <Typography variant="h5" sx={{ mt: 4, mb: 2, fontWeight: 700 }}>Top Scorers</Typography>
      <Grid container spacing={2}>
        {topScorers.map((p, i) => (
          <Grid item xs={12} md={4} key={i}>
            <Card>
              <CardContent>
                <Typography variant="h6">{p.name}</Typography>
                <Typography variant="body2" color="text.secondary">{p.team}</Typography>
                <Typography variant="h4" sx={{ mt: 1, color: '#00E5FF' }}>{p.goals} goals</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
