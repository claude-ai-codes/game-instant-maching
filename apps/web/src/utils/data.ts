import type { GameOption, RegionOption } from '@/types'

export const GAMES: GameOption[] = [
  { id: 'valorant', name: 'VALORANT' },
  { id: 'league_of_legends', name: 'League of Legends' },
  { id: 'apex_legends', name: 'Apex Legends' },
  { id: 'overwatch2', name: 'Overwatch 2' },
  { id: 'fortnite', name: 'Fortnite' },
  { id: 'splatoon3', name: 'Splatoon 3' },
  { id: 'street_fighter6', name: 'Street Fighter 6' },
  { id: 'pokemon_unite', name: 'Pokemon UNITE' },
  { id: 'marvel_rivals', name: 'Marvel Rivals' },
  { id: 'other', name: 'その他' },
]

export const REGIONS: RegionOption[] = [
  { id: 'jp', name: '日本' },
  { id: 'asia', name: 'アジア' },
  { id: 'na', name: '北米 (NA)' },
  { id: 'eu', name: 'ヨーロッパ (EU)' },
  { id: 'oce', name: 'オセアニア' },
  { id: 'other', name: 'その他' },
]

export function gameName(id: string): string {
  return GAMES.find(g => g.id === id)?.name ?? id
}

export function regionName(id: string): string {
  return REGIONS.find(r => r.id === id)?.name ?? id
}
