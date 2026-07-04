export interface Team {
  id: number
  name: string
  flag: string
  group: string
}

export interface Match {
  id: number
  homeTeamId: number
  awayTeamId: number
  date: string
  venue: string
  status: 'live' | 'finished' | 'upcoming'
  homeScore?: number
  awayScore?: number
  minute?: number
}

export interface Player {
  id: number
  name: string
  position: string
  teamId: number
  avatar: string
}

export interface ChampionPrediction {
  teamId: number
  probability: number
  reason: string
}
