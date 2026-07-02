export type UUID = string

export type User = {
  id: UUID
  username: string
  email?: string
  bio?: string | null
  profile_picture?: string | null
  codeforces_handle?: string | null
  rating: number
  is_admin?: boolean
  created_at: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type Tag = {
  id: UUID
  name: string
}

export type TestCase = {
  id: UUID
  input: string
  expected_output: string
  is_sample: boolean
}

export type ProblemListItem = {
  id: UUID
  title: string
  slug: string
  difficulty: 'Easy' | 'Medium' | 'Hard' | string
  tags: Tag[]
  solved_by_user?: boolean | null
}

export type PaginatedProblems = {
  items: ProblemListItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export type ProblemDetail = ProblemListItem & {
  description: string
  input_format: string
  output_format: string
  constraints: string
  test_cases: TestCase[]
  created_at: string
}

export type Submission = {
  id: UUID
  user_id: UUID
  problem_id: UUID
  language: string
  source_code: string
  verdict: string
  execution_time_ms?: number | null
  memory_used_kb?: number | null
  test_results?: unknown
  submitted_at: string
}

export type SubmissionList = {
  submissions: Submission[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export type RunResult = {
  stdout: string
  stderr: string
  verdict: string
  execution_time_ms: number
}

export type UserStats = {
  total_solved: number
  total_submissions: number
  easy_solved: number
  medium_solved: number
  hard_solved: number
  accuracy: number
  recent_submissions: Submission[]
}

export type TopicPerformance = {
  tag_name: string
  solved_count: number
  attempt_count: number
  accuracy: number
}

export type SubmissionHeatmap = {
  date: string
  count: number
}

export type DifficultyBreakdown = {
  easy_solved: number
  medium_solved: number
  hard_solved: number
  easy_total: number
  medium_total: number
  hard_total: number
}

export type WeakArea = {
  tag_name: string
  accuracy: number
  solved_count: number
  attempt_count: number
  suggestion: string
}

export type DashboardAnalytics = {
  topic_performance: TopicPerformance[]
  submission_heatmap: SubmissionHeatmap[]
  difficulty_breakdown: DifficultyBreakdown
  weak_areas: WeakArea[]
}

export type Friend = {
  friendship_id: UUID
  friend_id: UUID
  friend_username: string
  friend_rating: number
  friend_profile_picture?: string | null
}

export type FriendRequest = {
  id: UUID
  sender_id: UUID
  sender_username: string
  receiver_id: UUID
  receiver_username: string
  status: string
  created_at: string
}

export type Battle = {
  id: UUID
  host_user_id: UUID
  host_username: string
  opponent_user_id?: UUID | null
  opponent_username?: string | null
  problem_id: UUID
  problem_title: string
  problem_slug: string
  status: string
  winner_id?: UUID | null
  winner_username?: string | null
  duration_seconds: number
  started_at?: string | null
  ended_at?: string | null
  created_at: string
}

export type Notification = {
  id: UUID
  title: string
  message: string
  is_read: boolean
  notification_type: string
  reference_id?: string | null
  created_at: string
}

export type CodeforcesProfile = {
  handle: string
  rating: number
  max_rating: number
  rank?: string | null
  max_rank?: string | null
  last_synced_at: string
}

export type CodeforcesContest = {
  contest_id: number
  contest_name: string
  handle: string
  rank: number
  rating_change: number
  new_rating: number
  contest_date: string
}

export type LeaderboardRow = {
  rank: number
  user_id: UUID
  username: string
  rating: number
  profile_picture?: string | null
  total_solved?: number
}
