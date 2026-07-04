import { Box, Typography, Card, CardContent } from '@mui/material'
import { goalsPerMatch } from '../data/mock'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function History() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 800 }}>2026 Season History</Typography>
      
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Goals Trend — World Cup 2026</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={goalsPerMatch}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="goals" stroke="#00E5FF" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Box>
  )
}
