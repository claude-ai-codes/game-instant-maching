export interface User {
  id: string
  nickname: string
  created_at: string
}

export type PlayStyle = 'casual' | 'competitive' | 'beginner_welcome'

export interface Recruitment {
  id: string
  user_id: string
  game: string
  region: string
  start_time: string
  desired_role: string | null
  memo: string | null
  play_style: PlayStyle | null
  has_microphone: boolean
  status: 'open' | 'matched' | 'cancelled' | 'expired'
  expires_at: string
  created_at: string
  nickname: string | null
  thumbs_up_count: number
}

export interface Room {
  id: string
  recruitment_id: string
  status: 'active' | 'closed' | 'expired'
  expires_at: string
  created_at: string
  game: string | null
  region: string | null
  members: RoomMember[]
}

export interface RoomMember {
  user_id: string
  nickname: string
  role: string | null
  ready_to_close: boolean
}

export interface Message {
  id: string
  room_id: string
  user_id: string
  content: string
  created_at: string
  nickname: string | null
}

export interface GameOption {
  id: string
  name: string
}

export interface RegionOption {
  id: string
  name: string
}
