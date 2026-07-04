import { Team, Match, Player, ChampionPrediction } from '../types'

export const teams: Team[] = [
  { id: 1, name: 'France', flag: '🇫🇷', group: 'D' },
  { id: 2, name: 'Brazil', flag: '🇧🇷', group: 'B' },
  { id: 3, name: 'Argentina', flag: '🇦🇷', group: 'C' },
  { id: 4, name: 'England', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', group: 'B' },
  { id: 5, name: 'Spain', flag: '🇪🇸', group: 'A' },
  { id: 6, name: 'Germany', flag: '🇩🇪', group: 'A' },
  { id: 7, name: 'Portugal', flag: '🇵🇹', group: 'C' },
  { id: 8, name: 'Netherlands', flag: '🇳🇱', group: 'D' }
]

export const matches: Match[] = [
  { id: 101, homeTeamId: 1, awayTeamId: 2, date: '2026-07-10T20:00:00Z', venue: 'MetLife Stadium', status: 'live', homeScore: 2, awayScore: 1, minute: 67 },
  { id: 102, homeTeamId: 3, awayTeamId: 4, date: '2026-07-11T18:00:00Z', venue: 'SoFi Stadium', status: 'upcoming' },
  { id: 103, homeTeamId: 5, awayTeamId: 6, date: '2026-07-09T21:00:00Z', venue: 'AT&T Stadium', status: 'finished', homeScore: 3, awayScore: 0 }
]

export const players: Player[] = [
  { id: 1, name: 'Kylian Mbappé', position: 'FW', teamId: 1, avatar: '⚽' },
  { id: 2, name: 'Vinícius Júnior', position: 'FW', teamId: 2, avatar: '⚽' },
  { id: 3, name: 'Lionel Messi', position: 'FW', teamId: 3, avatar: '⚽' }
]

export const championPredictions: ChampionPrediction[] = [
  { teamId: 1, probability: 0.28, reason: 'Midfield depth + experience' },
  { teamId: 3, probability: 0.24, reason: 'Messi factor in knockout' },
  { teamId: 2, probability: 0.18, reason: 'Attacking firepower' },
  { teamId: 4, probability: 0.12, reason: 'Strong defense' },
  { teamId: 5, probability: 0.10, reason: 'Youth + form' },
  { teamId: 6, probability: 0.08, reason: 'Tactical discipline' }
]

export const goalsPerMatch = [
  { date: 'Jul 1', goals: 2.8 }, { date: 'Jul 2', goals: 3.1 }, { date: 'Jul 3', goals: 2.4 },
  { date: 'Jul 4', goals: 3.5 }, { date: 'Jul 5', goals: 2.9 }, { date: 'Jul 6', goals: 3.2 }
]

export const cardDistribution = [
  { stage: 'Group', yellow: 42, red: 3 }, { stage: 'R16', yellow: 28, red: 4 },
  { stage: 'QF', yellow: 18, red: 2 }, { stage: 'SF', yellow: 9, red: 1 }
]

export const topScorers = [
  { name: 'Mbappé', goals: 5, team: 'France' },
  { name: 'Messi', goals: 4, team: 'Argentina' },
  { name: 'Vinícius', goals: 4, team: 'Brazil' }
]
