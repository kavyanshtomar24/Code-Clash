import Editor from '@monaco-editor/react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  Bell,
  BookOpen,
  Braces,
  ChartNoAxesCombined,
  Check,
  ChevronRight,
  Code2,
  Flame,
  Gauge,
  LogOut,
  Medal,
  Play,
  Radar,
  Search,
  Send,
  Swords,
  UserPlus,
  Users,
  X,
} from 'lucide-react'
import { Component, useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, NavLink, Outlet, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar as RadarShape,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { z } from 'zod'
import { useAuth } from './context/useAuth'
import { endpoints, errorMessage } from './lib/api'
import type { Battle, ProblemDetail, ProblemListItem, Submission } from './lib/types'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: Gauge },
  { to: '/problems', label: 'Problems', icon: BookOpen },
  { to: '/analytics', label: 'Analytics', icon: ChartNoAxesCombined },
  { to: '/battles', label: 'Battles', icon: Swords },
  { to: '/friends', label: 'Friends', icon: Users },
  { to: '/leaderboard', label: 'Leaderboard', icon: Medal },
  { to: '/profile', label: 'Profile', icon: Radar },
]

const loginSchema = z.object({
  username_or_email: z.string().min(1, 'Username or email is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route element={<ProtectedShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/problems" element={<ProblemsPage />} />
          <Route path="/problems/:slug" element={<ProblemDetailPage />} />
          <Route path="/problems/:slug/ide" element={<IdePage />} />
          <Route path="/submissions" element={<SubmissionsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/friends" element={<FriendsPage />} />
          <Route path="/battles" element={<BattlesPage />} />
          <Route path="/battles/:id" element={<BattleRoomPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/profile/:username" element={<ProfilePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  )
}

function ProtectedShell() {
  const { isAuthenticated, isLoading, user, logout } = useAuth()
  const unread = useQuery({ queryKey: ['notifications', 'unread'], queryFn: endpoints.notifications.unread, enabled: isAuthenticated })

  if (isLoading) return <FullPageLoader />
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/dashboard" className="brand">
          <span className="brand-mark">CC</span>
          <span>CodeClash</span>
        </Link>
        <nav className="nav-list">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Engineering-grade performance platform</p>
            <h1>Code. Compete. Conquer.</h1>
          </div>
          <div className="topbar-actions">
            <Link className="icon-button" to="/notifications" title="Notifications">
              <Bell size={18} />
              {Boolean(unread.data?.unread_count) && <span className="badge">{unread.data?.unread_count}</span>}
            </Link>
            <Link className="profile-chip" to="/profile">
              <span>{user?.username}</span>
            </Link>
            <button className="icon-button" onClick={logout} title="Log out" type="button">
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  )
}

function LandingPage() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  return (
    <main className="landing blueprint-bg">
      <nav className="landing-nav">
        <Link to="/" className="brand"><span className="brand-mark">CC</span><span>CodeClash</span></Link>
        <div>
          <Link className="ghost-button" to="/login">Log in</Link>
          <Link className="primary-button" to="/register">Start competing</Link>
        </div>
      </nav>
      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">Engineering-grade performance platform</p>
          <h1>Code.<br /><span>Compete.</span><br />Conquer.</h1>
          <p>A precision-engineered competitive programming platform for real-time 1v1 battles, analytics, social accountability, and Codeforces-powered progress tracking.</p>
          <div className="hero-actions">
            <Link className="primary-button" to="/register">Create account <ChevronRight size={18} /></Link>
            <Link className="ghost-button" to="/login">Open control room</Link>
          </div>
        </div>
        <div className="hero-visual-group">
          <div className="engine-diagram hero-image-frame">
            <img
              src="/carnot-cycle.png"
              alt="Carnot cycle thermodynamic engine diagram showing energy input, thermal efficiency, and work output"
            />
          </div>
          <aside className="efficiency-annotation" aria-label="Engineering optimization metaphor">
            <p className="annotation-label">Optimization coefficient</p>
            <p className="annotation-formula">
              <span aria-hidden="true">η</span>
              <span className="sr-only">Efficiency equals</span>
              <span>=</span>
              <span>Problems Solved</span>
              <span aria-hidden="true">/</span>
              <span className="sr-only">divided by</span>
              <span>Effort Invested</span>
            </p>
            <p className="annotation-caption">
              Thermodynamics meets algorithms: turn focused effort into accepted solutions.
            </p>
          </aside>
        </div>
      </section>
      <section className="feature-band">
        {[
          ['Problems', 'Filterable DSA repository backed by live API data.'],
          ['IDE', 'Run samples and submit solutions through the judge pipeline.'],
          ['Battles', 'Private real-time rooms with shared timers and verdicts.'],
          ['Analytics', 'Topic balance, weak areas, difficulty split, and heatmaps.'],
        ].map(([title, text]) => (
          <article key={title} className="panel">
            <p className="eyebrow">{title}</p>
            <p>{text}</p>
          </article>
        ))}
      </section>
    </main>
  )
}

function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { login, register, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState('')
  const isLogin = mode === 'login'
  const form = useForm({
    resolver: zodResolver(isLogin ? loginSchema : registerSchema),
    defaultValues: isLogin ? { username_or_email: '', password: '' } : { username: '', email: '', password: '' },
  })

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  async function onSubmit(values: Record<string, string>) {
    setServerError('')
    try {
      if (isLogin) await login({ username_or_email: values.username_or_email, password: values.password })
      else await register({ username: values.username, email: values.email, password: values.password })
      navigate('/dashboard')
    } catch (error) {
      setServerError(errorMessage(error))
    }
  }

  return (
    <main className="auth-page blueprint-bg">
      <form className="auth-card" onSubmit={form.handleSubmit(onSubmit)}>
        <Link to="/" className="brand"><span className="brand-mark">CC</span><span>CodeClash</span></Link>
        <h1>{isLogin ? 'Open control room' : 'Create pilot profile'}</h1>
        {!isLogin && <TextInput label="Username" registration={form.register('username')} error={form.formState.errors.username?.message as string} />}
        {!isLogin && <TextInput label="Email" registration={form.register('email')} error={form.formState.errors.email?.message as string} />}
        {isLogin && <TextInput label="Username or email" registration={form.register('username_or_email')} error={form.formState.errors.username_or_email?.message as string} />}
        <TextInput label="Password" type="password" registration={form.register('password')} error={form.formState.errors.password?.message as string} />
        {serverError && <p className="form-error">{serverError}</p>}
        <button className="primary-button full" disabled={form.formState.isSubmitting} type="submit">
          {form.formState.isSubmitting ? 'Processing...' : isLogin ? 'Log in' : 'Register'}
        </button>
        <p className="muted">
          {isLogin ? 'Need an account?' : 'Already registered?'}{' '}
          <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Register' : 'Log in'}</Link>
        </p>
      </form>
    </main>
  )
}

function DashboardPage() {
  const stats = useQuery({ queryKey: ['users', 'stats'], queryFn: endpoints.users.stats })
  const analytics = useQuery({ queryKey: ['analytics'], queryFn: endpoints.analytics.dashboard })
  const problems = useQuery({ queryKey: ['problems', 'problems-dashboard'], queryFn: () => endpoints.problems.list({ per_page: 5 }) })
  const submissions = useQuery({ queryKey: ['submissions', 'history', 1], queryFn: () => endpoints.submissions.history({ per_page: 6 }) })

  return (
    <Page title="Dashboard" action={<Link className="primary-button" to="/problems">Solve Problems</Link>}>
      <MetricGrid
        items={[
          ['Solved', stats.data?.total_solved ?? 0, <Check size={20} />],
          ['Submissions', stats.data?.total_submissions ?? 0, <Activity size={20} />],
          ['Accuracy', `${Math.round(stats.data?.accuracy ?? 0)}%`, <Gauge size={20} />],
          [
            'Active Streak',
            `${analytics.data?.current_streak ?? 0} days (Max: ${analytics.data?.longest_streak ?? 0})`,
            <Flame size={20} style={{ color: (analytics.data?.current_streak ?? 0) > 0 ? '#f3c27b' : '#999' }} />,
          ],
        ]}
      />
      <div className="content-grid">
        <Panel title="Topic mastery radar" loading={analytics.isLoading}>
          <ChartBox>
            <ResponsiveContainer>
              <RadarChart data={analytics.data?.topic_performance ?? []}>
                <PolarGrid stroke="#2d2d2d" />
                <PolarAngleAxis dataKey="tag_name" tick={{ fill: '#b7b7b7', fontSize: 11 }} />
                <RadarShape dataKey="accuracy" stroke="#f3c27b" fill="#f3c27b" fillOpacity={0.22} />
                <Tooltip contentStyle={tooltipStyle} />
              </RadarChart>
            </ResponsiveContainer>
          </ChartBox>
        </Panel>
        <Panel title="Difficulty split" loading={analytics.isLoading}>
          <DifficultyBars data={analytics.data?.difficulty_breakdown} />
        </Panel>
      </div>
      <div className="content-grid">
        <Panel title="Active problem pool" loading={problems.isLoading}>
          <ProblemTable problems={problems.data?.items ?? []} compact />
        </Panel>
        <Panel title="Recent verdicts" loading={submissions.isLoading}>
          <SubmissionTable submissions={submissions.data?.submissions ?? []} />
        </Panel>
      </div>
    </Page>
  )
}

function ProblemsPage() {
  const [params, setParams] = useSearchParams()
  const query = {
    search: params.get('search') || undefined,
    difficulty: params.get('difficulty') || undefined,
    tag: params.get('tag') || undefined,
    status: params.get('status') || undefined,
    page: Number(params.get('page') || 1),
    per_page: 20,
  }
  const problems = useQuery({ queryKey: ['problems', query], queryFn: () => endpoints.problems.list(query) })
  const tags = useQuery({ queryKey: ['problem-tags'], queryFn: endpoints.problems.tags })

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.set('page', '1')
    setParams(next)
  }

  return (
    <Page title="Problem Repository" action={<Link className="ghost-button" to="/submissions">Submission Log</Link>}>
      <div className="filters">
        <label className="search-box"><Search size={17} /><input value={query.search ?? ''} onChange={(e) => update('search', e.target.value)} placeholder="Search problem titles" /></label>
        <select value={query.difficulty ?? ''} onChange={(e) => update('difficulty', e.target.value)}>
          <option value="">All difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <select value={query.tag ?? ''} onChange={(e) => update('tag', e.target.value)}>
          <option value="">All tags</option>
          {tags.data?.map((tag) => <option key={tag.id}>{tag.name}</option>)}
        </select>
        <select value={query.status ?? ''} onChange={(e) => update('status', e.target.value)}>
          <option value="">All statuses</option>
          <option value="solved">Solved</option>
          <option value="unsolved">Unsolved</option>
          <option value="attempted">Attempted</option>
        </select>
      </div>
      <Panel title={`${problems.data?.total ?? 0} calibrated problems`} loading={problems.isLoading}>
        <ProblemTable problems={problems.data?.items ?? []} />
      </Panel>
    </Page>
  )
}

function ProblemDetailPage() {
  const { slug = '' } = useParams()
  const problem = useQuery({ queryKey: ['problem', slug], queryFn: () => endpoints.problems.detail(slug), enabled: Boolean(slug) })
  const stats = useQuery({ queryKey: ['problem-stats', slug], queryFn: () => endpoints.problems.statistics(slug), enabled: Boolean(slug) })

  return (
    <Page title={problem.data?.title ?? 'Problem Detail'} action={problem.data && <Link className="primary-button" to={`/problems/${problem.data.slug}/ide`}>Open IDE</Link>}>
      <div className="content-grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <Panel title="Specification" loading={problem.isLoading}>
          {problem.data && <ProblemSpec problem={problem.data} />}
        </Panel>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Panel title="Solve metrics" loading={stats.isLoading}>
            {stats.data ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <MetricGrid
                  items={[
                    ['Solved rate', `${stats.data.solve_rate}%`, <Gauge size={16} />],
                    ['Solvers', stats.data.unique_solvers, <Users size={16} />],
                  ]}
                />
                <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#aaa', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Total Submissions</span>
                    <strong>{stats.data.total_submissions}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Accepted</span>
                    <strong style={{ color: '#68d391' }}>{stats.data.accepted}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Wrong Answer</span>
                    <strong style={{ color: '#fc8181' }}>{stats.data.wrong_answer}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Time Limit Exceeded</span>
                    <strong style={{ color: '#f6ad55' }}>{stats.data.tle}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Runtime Error</span>
                    <strong style={{ color: '#fc8181' }}>{stats.data.runtime_error}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Compile Error</span>
                    <strong style={{ color: '#cbd5e0' }}>{stats.data.compile_error}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState text="No statistics available." />
            )}
          </Panel>

          {stats.data && stats.data.language_breakdown.length > 0 && (
            <Panel title="Language split">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {stats.data.language_breakdown.map((lang) => (
                  <div key={lang.language} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                      <span style={{ textTransform: 'capitalize' }}>{lang.language}</span>
                      <span>{lang.count} ({lang.percentage}%)</span>
                    </div>
                    <div style={{ height: '6px', background: '#252525', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${lang.percentage}%`, background: '#f3c27b', borderRadius: '3px' }} />
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </Page>
  )
}

function IdePage() {
  const { slug = '' } = useParams()
  const problem = useQuery({ queryKey: ['problem', slug], queryFn: () => endpoints.problems.detail(slug), enabled: Boolean(slug) })
  const submissions = useQuery({ queryKey: ['submissions', problem.data?.id], queryFn: () => endpoints.submissions.byProblem(problem.data!.id), enabled: Boolean(problem.data?.id) })
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState(LANGUAGE_TEMPLATES.python)
  const [customInput, setCustomInput] = useState('')
  const [result, setResult] = useState('')
  const queryClient = useQueryClient()
  const isDefaultTemplate = Object.values(LANGUAGE_TEMPLATES).includes(code.trim())

  function handleLanguageChange(nextLanguage: string) {
    setLanguage(nextLanguage)
    if (isDefaultTemplate) {
      setCode(LANGUAGE_TEMPLATES[nextLanguage] ?? LANGUAGE_TEMPLATES.python)
    }
  }

  const run = useMutation({
    mutationFn: () => endpoints.submissions.run({ problem_id: problem.data!.id, language, code, input: customInput }),
    onSuccess: (data) => setResult(`${data.verdict}\n\nstdout:\n${data.stdout || '-'}\n\nstderr:\n${data.stderr || '-'}`),
    onError: (error) => setResult(errorMessage(error)),
  })
  const submit = useMutation({
    mutationFn: () => endpoints.submissions.submit({ problem_id: problem.data!.id, language, code }),
    onSuccess: (data) => {
      setResult(`Submission queued: ${data.verdict}`)
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
    onError: (error) => setResult(errorMessage(error)),
  })

  return (
    <Page title={problem.data?.title ?? 'Online IDE'}>
      <div className="ide-grid">
        <Panel title="Problem" loading={problem.isLoading}>{problem.data && <ProblemSpec problem={problem.data} compact />}</Panel>
        <Panel title="Execution Console">
          <div className="ide-toolbar">
            <select value={language} onChange={(e) => handleLanguageChange(e.target.value)}>
              <option value="python">Python</option>
              <option value="cpp">C++</option>
              <option value="java">Java</option>
            </select>
            <button className="ghost-button" disabled={!problem.data || run.isPending} onClick={() => run.mutate()} type="button"><Play size={16} /> Run</button>
            <button className="primary-button" disabled={!problem.data || submit.isPending} onClick={() => submit.mutate()} type="button"><Send size={16} /> Submit</button>
          </div>
          <div className="editor-frame">
            <Editor height="420px" language={language === 'cpp' ? 'cpp' : language} theme="vs-dark" value={code} onChange={(value) => setCode(value ?? '')} options={{ minimap: { enabled: false }, fontSize: 14 }} />
          </div>
          <textarea value={customInput} onChange={(e) => setCustomInput(e.target.value)} placeholder="Custom input" className="console-input" />
          <pre className="output-panel">{result || 'Execution output will appear here.'}</pre>
          <SubmissionTable submissions={submissions.data ?? []} />
        </Panel>
      </div>
    </Page>
  )
}

const LANGUAGE_TEMPLATES: Record<string, string> = {
  python: `def solve():
    pass

solve()`,
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return 0;
}`,
  java: `import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

    }
}`,
}

function AnalyticsPage() {
  const analytics = useQuery({ queryKey: ['analytics'], queryFn: endpoints.analytics.dashboard })
  return (
    <Page title="Analytics Suite">
      <div className="content-grid">
        <Panel title="Submission heatmap" loading={analytics.isLoading}>
          <ChartBox><ResponsiveContainer><AreaChart data={analytics.data?.submission_heatmap ?? []}><CartesianGrid stroke="#252525" /><XAxis dataKey="date" tick={{ fill: '#999', fontSize: 10 }} /><YAxis tick={{ fill: '#999', fontSize: 10 }} /><Tooltip contentStyle={tooltipStyle} /><Area dataKey="count" stroke="#f3c27b" fill="#f3c27b" fillOpacity={0.22} /></AreaChart></ResponsiveContainer></ChartBox>
        </Panel>
        <Panel title="Topic accuracy" loading={analytics.isLoading}>
          <ChartBox><ResponsiveContainer><BarChart data={analytics.data?.topic_performance ?? []}><CartesianGrid stroke="#252525" /><XAxis dataKey="tag_name" tick={{ fill: '#999', fontSize: 10 }} /><YAxis tick={{ fill: '#999', fontSize: 10 }} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="accuracy" fill="#f3c27b" /></BarChart></ResponsiveContainer></ChartBox>
        </Panel>
      </div>
      <Panel title="Weak areas" loading={analytics.isLoading}>
        <div className="card-list">
          {(analytics.data?.weak_areas ?? []).map((area) => (
            <article key={area.tag_name} className="mini-card">
              <strong>{area.tag_name}</strong>
              <span>{Math.round(area.accuracy)}% accuracy</span>
              <p>{area.suggestion}</p>
            </article>
          ))}
        </div>
      </Panel>
    </Page>
  )
}

function FriendsPage() {
  const queryClient = useQueryClient()
  const [username, setUsername] = useState('')
  const friends = useQuery({ queryKey: ['friends'], queryFn: endpoints.friends.list })
  const requests = useQuery({ queryKey: ['friend-requests'], queryFn: endpoints.friends.requests })
  const sendRequest = useMutation({ mutationFn: endpoints.friends.request, onSuccess: () => { setUsername(''); queryClient.invalidateQueries({ queryKey: ['friend-requests'] }) } })
  const action = useMutation({ mutationFn: ({ id, type }: { id: string; type: 'accept' | 'reject' }) => type === 'accept' ? endpoints.friends.accept(id) : endpoints.friends.reject(id), onSuccess: () => queryClient.invalidateQueries() })

  return (
    <Page title="Friends Network">
      <Panel title="Dispatch connection request">
        <form className="inline-form" onSubmit={(e) => { e.preventDefault(); if (username) sendRequest.mutate(username) }}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
          <button className="primary-button" type="submit"><UserPlus size={16} /> Send</button>
        </form>
        {sendRequest.error && <p className="form-error">{errorMessage(sendRequest.error)}</p>}
      </Panel>
      <div className="content-grid">
        <Panel title="Active friends" loading={friends.isLoading}>
          <div className="card-list">
            {(friends.data ?? []).map((friend) => (
              <article key={friend.friend_id} className="mini-card horizontal">
                <div><strong>{friend.friend_username}</strong><span>{friend.friend_rating} rating</span></div>
                <Link className="ghost-button" to={`/profile/${friend.friend_username}`}>Compare</Link>
              </article>
            ))}
          </div>
        </Panel>
        <Panel title="Pending requests" loading={requests.isLoading}>
          <div className="card-list">
            {(requests.data ?? []).map((request) => (
              <article key={request.id} className="mini-card horizontal">
                <div><strong>{request.sender_username}</strong><span>{request.status}</span></div>
                <div className="row-actions">
                  <button className="icon-button" onClick={() => action.mutate({ id: request.id, type: 'accept' })} title="Accept" type="button"><Check size={16} /></button>
                  <button className="icon-button" onClick={() => action.mutate({ id: request.id, type: 'reject' })} title="Reject" type="button"><X size={16} /></button>
                </div>
              </article>
            ))}
          </div>
        </Panel>
      </div>
    </Page>
  )
}

function BattlesPage() {
  const queryClient = useQueryClient()
  const [problemId, setProblemId] = useState('')
  const [opponent, setOpponent] = useState('')
  const [battleNotice, setBattleNotice] = useState('')
  const battles = useQuery({ queryKey: ['battles'], queryFn: endpoints.battles.history })
  const problems = useQuery({ queryKey: ['problems', 'battle-select'], queryFn: () => endpoints.problems.list({ per_page: 100 }) })
  const create = useMutation({
    mutationFn: () => endpoints.battles.create({ problem_id: problemId, duration_seconds: 1800, opponent_username: opponent || undefined }),
    onSuccess: (battle) => { queryClient.invalidateQueries({ queryKey: ['battles'] }); window.location.href = `/battles/${battle.id}` },
  })
  const endBattle = useMutation({
    mutationFn: endpoints.battles.end,
    onSuccess: (battle) => {
      queryClient.invalidateQueries({ queryKey: ['battles'] })
      queryClient.invalidateQueries({ queryKey: ['battle', battle.id] })
      setBattleNotice(`Battle ${battle.status === 'cancelled' ? 'cancelled' : 'ended'} successfully.`)
    },
    onError: (error) => setBattleNotice(errorMessage(error)),
  })

  function handleEndBattle(battle: Battle) {
    setBattleNotice('')
    const action = battle.status === 'pending' ? 'cancel this battle lobby' : 'end this battle as a draw'
    if (window.confirm(`Are you sure you want to ${action}?`)) {
      endBattle.mutate(battle.id)
    }
  }

  return (
    <Page title="Battle Arena">
      <Panel title="Create private lobby">
        <form className="inline-form" onSubmit={(e) => { e.preventDefault(); if (problemId) create.mutate() }}>
          <select value={problemId} onChange={(e) => setProblemId(e.target.value)}>
            <option value="">Select problem</option>
            {problems.data?.items.map((problem) => <option key={problem.id} value={problem.id}>{problem.title}</option>)}
          </select>
          <input value={opponent} onChange={(e) => setOpponent(e.target.value)} placeholder="Opponent username optional" />
          <button className="primary-button" type="submit"><Swords size={16} /> Create</button>
        </form>
        {create.error && <p className="form-error">{errorMessage(create.error)}</p>}
      </Panel>
      <Panel title="Battle history" loading={battles.isLoading}>
        {battleNotice && <p className={endBattle.isError ? 'form-error' : 'status-message'}>{battleNotice}</p>}
        <BattleList battles={battles.data ?? []} endingBattleId={endBattle.variables} onEndBattle={handleEndBattle} />
      </Panel>
    </Page>
  )
}

function BattleRoomPage() {
  const queryClient = useQueryClient()
  const { id = '' } = useParams()
  const { user } = useAuth()
  const [battleNotice, setBattleNotice] = useState('')
  const battle = useQuery({ queryKey: ['battle', id], queryFn: () => endpoints.battles.detail(id), enabled: Boolean(id) })
  const problem = useQuery({ queryKey: ['problem', battle.data?.problem_slug], queryFn: () => endpoints.problems.detail(battle.data!.problem_slug), enabled: Boolean(battle.data?.problem_slug) })
  
  const joinBattle = useMutation({
    mutationFn: () => endpoints.battles.join(id),
    onSuccess: (updatedBattle) => {
      queryClient.setQueryData(['battle', id], updatedBattle)
      queryClient.invalidateQueries({ queryKey: ['battles'] })
    },
    onError: (error) => setBattleNotice(errorMessage(error)),
  })

  const endBattle = useMutation({
    mutationFn: endpoints.battles.end,
    onSuccess: (ended) => {
      queryClient.setQueryData(['battle', id], ended)
      queryClient.invalidateQueries({ queryKey: ['battles'] })
      setBattleNotice(`Battle ${ended.status === 'cancelled' ? 'cancelled' : 'ended'} successfully.`)
    },
    onError: (error) => setBattleNotice(errorMessage(error)),
  })
  const canEndBattle = battle.data ? isEndableBattle(battle.data) : false

  function handleEndBattle() {
    if (!battle.data) return
    setBattleNotice('')
    const action = battle.data.status === 'pending' ? 'cancel this battle lobby' : 'end this battle as a draw'
    if (window.confirm(`Are you sure you want to ${action}?`)) {
      endBattle.mutate(battle.data.id)
    }
  }

  const isHost = battle.data?.host_user_id === user?.id
  const isPending = battle.data?.status === 'pending'
  const isParticipant = battle.data?.host_user_id === user?.id || battle.data?.opponent_user_id === user?.id

  return (
    <Page
      title="Live Battle Room"
      action={battle.data && (
        <button className="ghost-button" disabled={!canEndBattle || endBattle.isPending} onClick={handleEndBattle} type="button">
          <X size={16} /> {endBattle.isPending ? 'Ending...' : 'End Battle'}
        </button>
      )}
    >
      <div className="content-grid">
        {battle.data?.status === 'finished' && (
          <div className="battle-result-banner" style={{ gridColumn: '1 / -1', background: 'linear-gradient(135deg, rgba(243,194,123,0.12), rgba(243,194,123,0.04))', border: '1px solid rgba(243,194,123,0.3)', borderRadius: '12px', padding: '2rem', textAlign: 'center', marginBottom: '0.5rem' }}>
            <p style={{ fontSize: '14px', color: '#b9b9b9', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '1px' }}>Battle Complete</p>
            <h2 style={{ fontSize: '28px', color: '#f6f6f6', margin: '0 0 0.5rem' }}>
              {battle.data.winner_username
                ? `🏆 ${battle.data.winner_username} Wins!`
                : '🤝 Draw — No Winner'}
            </h2>
            {battle.data.winner_id && (
              <p style={{ color: battle.data.winner_id === user?.id ? '#5ee87a' : '#f87171', fontSize: '16px', fontWeight: 600 }}>
                {battle.data.winner_id === user?.id ? 'Congratulations, you won! (+50 rating)' : 'Better luck next time (-20 rating)'}
              </p>
            )}
          </div>
        )}
        <Panel title="Match telemetry" loading={battle.isLoading}>
          {battleNotice && <p className={endBattle.isError ? 'form-error' : 'status-message'}>{battleNotice}</p>}
          {battle.data && <BattleTelemetry battle={battle.data} />}
          
          {battle.data && isPending && !isHost && (
            <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
              <button
                className="primary-button full"
                onClick={() => joinBattle.mutate()}
                disabled={joinBattle.isPending}
                style={{ padding: '1rem' }}
                type="button"
              >
                {joinBattle.isPending ? 'Joining Battle...' : 'Accept & Join Battle'}
              </button>
              {joinBattle.error && <p className="form-error" style={{ marginTop: '0.5rem' }}>{errorMessage(joinBattle.error)}</p>}
            </div>
          )}
        </Panel>
        <Panel title="Problem package" loading={problem.isLoading}>
          {problem.data && <ProblemSpec problem={problem.data} compact />}
          {battle.data && (
            isPending && !isHost ? (
              <button
                className="primary-button"
                onClick={() => joinBattle.mutate()}
                disabled={joinBattle.isPending}
                type="button"
              >
                {joinBattle.isPending ? 'Joining...' : 'Join Battle'}
              </button>
            ) : (
              battle.data.status === 'active' && isParticipant && (
                <Link className="primary-button" to={`/problems/${battle.data.problem_slug}/ide`}>Open battle IDE</Link>
              )
            )
          )}
        </Panel>
      </div>
    </Page>
  )
}

function SubmissionsPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page') || 1)
  const verdict = params.get('verdict') || undefined
  const language = params.get('language') || undefined

  const submissions = useQuery({
    queryKey: ['submissions', 'history', { page, verdict, language }],
    queryFn: () => endpoints.submissions.history({ page, per_page: 20, verdict, language }),
  })

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.set('page', '1')
    setParams(next)
  }

  const data = submissions.data
  const list = data?.submissions ?? []
  const totalPages = data?.total_pages ?? 1

  return (
    <Page title="Submission Log">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="filters">
          <select value={verdict ?? ''} onChange={(e) => update('verdict', e.target.value)}>
            <option value="">All verdicts</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="WRONG_ANSWER">Wrong Answer</option>
            <option value="TIME_LIMIT_EXCEEDED">Time Limit Exceeded</option>
            <option value="RUNTIME_ERROR">Runtime Error</option>
            <option value="COMPILE_ERROR">Compile Error</option>
          </select>
          <select value={language ?? ''} onChange={(e) => update('language', e.target.value)}>
            <option value="">All languages</option>
            <option value="python">Python</option>
            <option value="cpp">C++</option>
            <option value="java">Java</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
          </select>
        </div>

        <Panel title="Judge history" loading={submissions.isLoading}>
          <SubmissionTable submissions={list} />
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1.5rem' }}>
              <button
                className="ghost-button"
                disabled={page <= 1}
                onClick={() => {
                  const next = new URLSearchParams(params)
                  next.set('page', String(page - 1))
                  setParams(next)
                }}
                type="button"
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
                if (totalPages > 7 && Math.abs(p - page) > 2 && p !== 1 && p !== totalPages) {
                  if (p === 2 || p === totalPages - 1) {
                    return <span key={p} style={{ alignSelf: 'center', color: '#555' }}>...</span>
                  }
                  return null
                }
                return (
                  <button
                    key={p}
                    className={p === page ? 'primary-button' : 'ghost-button'}
                    style={{ minWidth: '40px', padding: '0.5rem' }}
                    onClick={() => {
                      const next = new URLSearchParams(params)
                      next.set('page', String(p))
                      setParams(next)
                    }}
                    type="button"
                  >
                    {p}
                  </button>
                )
              })}
              <button
                className="ghost-button"
                disabled={page >= totalPages}
                onClick={() => {
                  const next = new URLSearchParams(params)
                  next.set('page', String(page + 1))
                  setParams(next)
                }}
                type="button"
              >
                Next
              </button>
            </div>
          )}
        </Panel>
      </div>
    </Page>
  )
}

function NotificationsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const notifications = useQuery({ queryKey: ['notifications'], queryFn: endpoints.notifications.list })
  const read = useMutation({ mutationFn: endpoints.notifications.read, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }) })
  const readAll = useMutation({ mutationFn: endpoints.notifications.readAll, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }) })
  
  const joinBattle = useMutation({
    mutationFn: endpoints.battles.join,
    onSuccess: (battle) => {
      navigate(`/battles/${battle.id}`)
    },
    onError: (err) => {
      alert(errorMessage(err))
    }
  })

  return (
    <Page title="Notifications" action={<button className="ghost-button" onClick={() => readAll.mutate()} type="button">Mark all read</button>}>
      <Panel title="Event tray" loading={notifications.isLoading}>
        <div className="card-list">
          {(notifications.data ?? []).map((item) => (
            <article key={item.id} className={item.is_read ? 'mini-card' : 'mini-card unread'}>
              <strong>{item.title}</strong>
              <span>{item.notification_type}</span>
              <p>{item.message}</p>
              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                {item.notification_type === 'battle_invite' && item.reference_id && (
                  <>
                    <button
                      className="primary-button"
                      style={{ minHeight: '32px', height: '32px', padding: '0 12px', fontSize: '13px' }}
                      onClick={() => joinBattle.mutate(item.reference_id!)}
                      disabled={joinBattle.isPending}
                      type="button"
                    >
                      {joinBattle.isPending ? 'Joining...' : 'Accept & Join'}
                    </button>
                    <Link
                      className="ghost-button"
                      style={{ minHeight: '32px', height: '32px', padding: '0 12px', fontSize: '13px' }}
                      to={`/battles/${item.reference_id}`}
                    >
                      View Room
                    </Link>
                  </>
                )}
                {item.notification_type === 'friend_request' && (
                  <Link
                    className="primary-button"
                    style={{ minHeight: '32px', height: '32px', padding: '0 12px', fontSize: '13px' }}
                    to="/friends"
                  >
                    View Requests
                  </Link>
                )}
                {!item.is_read && (
                  <button
                    className="ghost-button"
                    style={{ minHeight: '32px', height: '32px', padding: '0 12px', fontSize: '13px' }}
                    onClick={() => read.mutate(item.id)}
                    type="button"
                  >
                    Mark read
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </Page>
  )
}

function LeaderboardPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = parseInt(searchParams.get('page') || '1', 10)
  const sortBy = searchParams.get('sort_by') || 'rating'
  const search = searchParams.get('search') || ''

  const [searchInput, setSearchInput] = useState(search)

  // Sync search input with search param debounced
  useEffect(() => {
    const handler = setTimeout(() => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        if (searchInput.trim()) {
          next.set('search', searchInput.trim())
        } else {
          next.delete('search')
        }
        next.set('page', '1')
        return next
      })
    }, 300)
    return () => clearTimeout(handler)
  }, [searchInput, setSearchParams])

  const leaderboard = useQuery({
    queryKey: ['leaderboard', { page, sortBy, search }],
    queryFn: () => endpoints.leaderboard.list({ page, per_page: 20, search, sort_by: sortBy }),
  })

  const handlePageChange = (newPage: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('page', newPage.toString())
      return next
    })
  }

  const handleSortChange = (field: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('sort_by', field)
      next.set('page', '1')
      return next
    })
  }

  const data = leaderboard.data
  const users = data?.users ?? []
  const totalPages = data?.total_pages ?? 1
  const totalUsers = data?.total_users ?? 0
  const startRow = (page - 1) * 20 + 1
  const endRow = Math.min(page * 20, totalUsers)

  return (
    <Page title="Leaderboard">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Controls Panel */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="field" style={{ margin: 0, width: '100%', maxWidth: '350px', position: 'relative' }}>
            <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#888', display: 'flex', alignItems: 'center' }}>
              <Search size={16} />
            </span>
            <input
              type="text"
              placeholder="Search users..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              style={{ paddingLeft: '2.5rem', margin: 0 }}
            />
          </div>
          <div style={{ color: '#888', fontSize: '0.9rem' }}>
            {totalUsers > 0 ? `Showing ${startRow}–${endRow} of ${totalUsers} users` : 'No users found'}
          </div>
        </div>

        <Panel title="Global Rankings" loading={leaderboard.isLoading}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Rank</th>
                  <th>User</th>
                  <th
                    onClick={() => handleSortChange('rating')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    Rating {sortBy === 'rating' ? '▼' : '⇅'}
                  </th>
                  <th
                    onClick={() => handleSortChange('solved')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    Solved {sortBy === 'solved' ? '▼' : '⇅'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map((row) => (
                  <tr key={row.user_id}>
                    <td>
                      <strong style={{ color: row.rank <= 3 ? '#f3c27b' : '#aaa' }}>
                        #{row.rank}
                      </strong>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        {row.profile_picture ? (
                          <img
                            src={row.profile_picture}
                            alt={row.username}
                            style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover', border: '1px solid rgba(255,255,255,0.1)' }}
                          />
                        ) : (
                          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, #3a3f58, #23273a)', color: '#f3c27b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.85rem', border: '1px solid rgba(255,255,255,0.1)' }}>
                            {row.username.slice(0, 2).toUpperCase()}
                          </div>
                        )}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                          <Link to={`/profile/${row.username}`} style={{ fontWeight: 600 }}>
                            {row.username}
                          </Link>
                          {row.codeforces_handle && (
                            <span style={{ fontSize: '0.75rem', color: '#68d391' }}>
                              cf: {row.codeforces_handle}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'rgba(243, 194, 123, 0.1)', color: '#f3c27b', border: '1px solid rgba(243, 194, 123, 0.2)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontWeight: 'bold' }}>
                        {row.rating}
                      </span>
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'rgba(255,255,255,0.05)', color: '#aaa', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
                        {row.total_solved} solved
                      </span>
                    </td>
                  </tr>
                ))}
                {!leaderboard.isLoading && users.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: '3rem 0', color: '#888' }}>
                      No matching records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1.5rem' }}>
              <button
                className="ghost-button"
                disabled={page <= 1}
                onClick={() => handlePageChange(page - 1)}
                type="button"
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
                if (totalPages > 7 && Math.abs(p - page) > 2 && p !== 1 && p !== totalPages) {
                  if (p === 2 || p === totalPages - 1) {
                    return <span key={p} style={{ alignSelf: 'center', color: '#555' }}>...</span>
                  }
                  return null
                }
                return (
                  <button
                    key={p}
                    className={p === page ? 'primary-button' : 'ghost-button'}
                    style={{ minWidth: '40px', padding: '0.5rem' }}
                    onClick={() => handlePageChange(p)}
                    type="button"
                  >
                    {p}
                  </button>
                )
              })}
              <button
                className="ghost-button"
                disabled={page >= totalPages}
                onClick={() => handlePageChange(page + 1)}
                type="button"
              >
                Next
              </button>
            </div>
          )}
        </Panel>
      </div>
    </Page>
  )
}

function ProfilePage() {
  const { username } = useParams()
  const { user } = useAuth()
  const viewed = username ?? user?.username ?? ''
  
  const profile = useQuery({ queryKey: ['profile', viewed], queryFn: () => endpoints.users.profile(viewed), enabled: Boolean(viewed) && viewed !== user?.username })
  const stats = useQuery({ queryKey: ['stats', viewed], queryFn: () => viewed === user?.username ? endpoints.users.stats() : endpoints.users.publicStats(viewed), enabled: Boolean(viewed) })
  const cf = useQuery({ queryKey: ['codeforces'], queryFn: endpoints.codeforces.profile, enabled: viewed === user?.username, retry: false })
  const ratingHistory = useQuery({
    queryKey: ['ratingHistory', viewed],
    queryFn: () => viewed === user?.username ? endpoints.users.ratingHistory() : endpoints.users.ratingHistoryByUsername(viewed),
    enabled: Boolean(viewed),
  })
  
  // Only display battles/contests for own profile or where API permits
  const battleHistory = useQuery({
    queryKey: ['battleHistory', viewed],
    queryFn: () => endpoints.users.battleHistory({ per_page: 10 }),
    enabled: viewed === user?.username,
  })
  const cfContests = useQuery({
    queryKey: ['cfContests', viewed],
    queryFn: endpoints.codeforces.contests,
    enabled: viewed === user?.username && Boolean(user?.codeforces_handle),
    retry: false,
  })

  const display = viewed === user?.username ? user : profile.data
  const codeforcesHandle = display?.codeforces_handle || cf.data?.handle
  const codeforcesRating = cf.data?.rating ?? display?.rating ?? 0
  const codeforcesRank = cf.data?.rank ?? 'Not ranked'

  return (
    <Page title={display?.username ?? 'Profile'} action={viewed === user?.username && <Link className="ghost-button" to="/settings">Edit profile</Link>}>
      <MetricGrid variant="three" items={[['Solved', stats.data?.total_solved ?? 0, <Check size={20} />], ['Accuracy', `${Math.round(stats.data?.accuracy ?? 0)}%`, <Activity size={20} />], ['Submissions', stats.data?.total_submissions ?? 0, <Braces size={20} />]]} />
      
      <div className="content-grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Panel title="Rating trajectory" loading={ratingHistory.isLoading}>
            {ratingHistory.data && ratingHistory.data.length > 0 ? (
              <ChartBox>
                <ResponsiveContainer>
                  <LineChart data={ratingHistory.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#252525" />
                    <XAxis
                      dataKey="recorded_at"
                      tickFormatter={(str) => new Date(str).toLocaleDateString()}
                      tick={{ fill: '#999', fontSize: 10 }}
                    />
                    <YAxis tick={{ fill: '#999', fontSize: 10 }} domain={['dataMin - 50', 'dataMax + 50']} />
                    <Tooltip
                      contentStyle={tooltipStyle}
                      labelFormatter={(str) => new Date(str).toLocaleString()}
                    />
                    <Line
                      type="monotone"
                      dataKey="rating"
                      stroke="#f3c27b"
                      strokeWidth={2}
                      dot={{ r: 3, fill: '#161925', stroke: '#f3c27b', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartBox>
            ) : (
              <EmptyState text="No battle rating changes recorded yet." />
            )}
          </Panel>

          {viewed === user?.username && (
            <Panel title="Battle chronicle" loading={battleHistory.isLoading}>
              {battleHistory.data && battleHistory.data.battles.length > 0 ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Outcome</th>
                        <th>Opponent</th>
                        <th>Problem</th>
                        <th>Rating delta</th>
                        <th>Ended</th>
                      </tr>
                    </thead>
                    <tbody>
                      {battleHistory.data.battles.map((b) => (
                        <tr key={b.battle_id}>
                          <td>
                            <span
                              className="badge"
                              style={{
                                background:
                                  b.outcome === 'won'
                                    ? 'rgba(104, 211, 145, 0.1)'
                                    : b.outcome === 'lost'
                                    ? 'rgba(252, 129, 129, 0.1)'
                                    : 'rgba(255, 255, 255, 0.05)',
                                color:
                                  b.outcome === 'won'
                                    ? '#68d391'
                                    : b.outcome === 'lost'
                                    ? '#fc8181'
                                    : '#aaa',
                              }}
                            >
                              {b.outcome.toUpperCase()}
                            </span>
                          </td>
                          <td>{b.opponent_username}</td>
                          <td>
                            <Link to={`/problems/${b.problem_slug}`}>{b.problem_title}</Link>
                          </td>
                          <td>
                            <strong style={{ color: b.rating_change >= 0 ? '#68d391' : '#fc8181' }}>
                              {b.rating_change >= 0 ? `+${b.rating_change}` : b.rating_change}
                            </strong>
                          </td>
                          <td>{b.ended_at ? new Date(b.ended_at).toLocaleDateString() : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState text="No competitive battle participations logged." />
              )}
            </Panel>
          )}

          {viewed === user?.username && user?.codeforces_handle && (
            <Panel title="Codeforces Contest Performance" loading={cfContests.isLoading}>
              {cfContests.data && cfContests.data.length > 0 ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Contest</th>
                        <th>Rank</th>
                        <th>Rating Change</th>
                        <th>New Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cfContests.data.map((c) => (
                        <tr key={c.contest_id}>
                          <td>{c.contest_name}</td>
                          <td>#{c.rank}</td>
                          <td>
                            <strong style={{ color: c.rating_change >= 0 ? '#68d391' : '#fc8181' }}>
                              {c.rating_change >= 0 ? `+${c.rating_change}` : c.rating_change}
                            </strong>
                          </td>
                          <td>{c.new_rating}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState text="No Codeforces contests synchronised." />
              )}
            </Panel>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Panel title="Codeforces profile" loading={cf.isLoading && viewed === user?.username}>
            {codeforcesHandle ? (
              <div className="codeforces-grid" style={{ display: 'grid', gap: '1rem' }}>
                <article className="codeforces-card">
                  <span><Code2 size={18} /> Handle</span>
                  <strong>{codeforcesHandle}</strong>
                </article>
                <article className="codeforces-card">
                  <span><Gauge size={18} /> Rating</span>
                  <strong>{codeforcesRating}</strong>
                </article>
                <article className="codeforces-card">
                  <span><Medal size={18} /> Rank</span>
                  <strong>{codeforcesRank}</strong>
                </article>
              </div>
            ) : (
              <EmptyState text="No linked Codeforces profile yet." />
            )}
          </Panel>
          <Panel title="Profile dossier">
            <p>{display?.bio || 'No bio configured yet.'}</p>
            <p className="muted">Codeforces: {codeforcesHandle || 'Not linked'}</p>
          </Panel>
        </div>
      </div>
    </Page>
  )
}

function SettingsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [bio, setBio] = useState(user?.bio ?? '')
  const [picture, setPicture] = useState(user?.profile_picture ?? '')
  const [handle, setHandle] = useState(user?.codeforces_handle ?? '')
  const cf = useQuery({ queryKey: ['codeforces'], queryFn: endpoints.codeforces.profile, retry: false })
  const effectiveHandle = handle || cf.data?.handle || ''
  const update = useMutation({ mutationFn: () => endpoints.users.update({ bio, profile_picture: picture, codeforces_handle: effectiveHandle }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth'] }) })
  const link = useMutation({ mutationFn: () => endpoints.codeforces.link(effectiveHandle), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['codeforces'] }); queryClient.invalidateQueries({ queryKey: ['auth'] }) } })
  const sync = useMutation({ mutationFn: endpoints.codeforces.sync, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['codeforces'] }) })

  return (
    <Page title="Settings">
      <Panel title="Account configuration">
        <div className="settings-form">
          <label>Bio<textarea value={bio} onChange={(e) => setBio(e.target.value)} /></label>
          <label>Profile picture URL<input value={picture} onChange={(e) => setPicture(e.target.value)} /></label>
          <label>Codeforces handle<input value={effectiveHandle} onChange={(e) => setHandle(e.target.value)} /></label>
          <div className="row-actions">
            <button className="primary-button" onClick={() => update.mutate()} type="button">Save profile</button>
            <button className="ghost-button" onClick={() => link.mutate()} type="button">Link handle</button>
            <button className="ghost-button" onClick={() => sync.mutate()} type="button">Sync Codeforces</button>
          </div>
          {[update.error, link.error, sync.error].filter(Boolean).map((error, index) => <p className="form-error" key={index}>{errorMessage(error)}</p>)}
        </div>
      </Panel>
      <Panel title="Codeforces cache" loading={cf.isLoading}>
        {cf.data ? <MetricGrid items={[['Handle', cf.data.handle, <Code2 size={20} />], ['Rating', cf.data.rating, <Gauge size={20} />], ['Max rating', cf.data.max_rating, <Flame size={20} />], ['Rank', cf.data.rank ?? '-', <Medal size={20} />]]} /> : <EmptyState text="No linked Codeforces profile yet." />}
      </Panel>
    </Page>
  )
}

function Page({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="page">
      <div className="page-heading">
        <div><p className="eyebrow">Control surface</p><h2>{title}</h2></div>
        {action}
      </div>
      {children}
    </section>
  )
}

function Panel({ title, loading, children }: { title: string; loading?: boolean; children: React.ReactNode }) {
  return <section className="panel"><div className="panel-heading"><h3>{title}</h3></div>{loading ? <Skeleton /> : children}</section>
}

function MetricGrid({ items, variant }: { items: Array<[string, React.ReactNode, React.ReactNode]>; variant?: 'three' }) {
  return <div className={variant === 'three' ? 'metric-grid metric-grid-three' : 'metric-grid'}>{items.map(([label, value, icon]) => <article className="metric-card" key={label}><span>{icon}</span><p>{label}</p><strong>{value}</strong></article>)}</div>
}

function ProblemTable({ problems, compact }: { problems: ProblemListItem[]; compact?: boolean }) {
  if (!problems.length) return <EmptyState text="No problems returned by the API." />
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Status</th><th>Problem</th><th>Difficulty</th>{!compact && <th>Tags</th>}<th></th></tr></thead>
        <tbody>
          {problems.map((problem) => <tr key={problem.id}><td>{problem.solved_by_user ? 'Solved' : 'Open'}</td><td><Link to={`/problems/${problem.slug}`}>{problem.title}</Link></td><td><Difficulty value={problem.difficulty} /></td>{!compact && <td>{problem.tags.map((tag) => <span className="tag" key={tag.id}>{tag.name}</span>)}</td>}<td><Link className="icon-button" to={`/problems/${problem.slug}/ide`} title="Open IDE"><Code2 size={16} /></Link></td></tr>)}
        </tbody>
      </table>
    </div>
  )
}

function SubmissionTable({ submissions }: { submissions: Submission[] }) {
  if (!submissions.length) return <EmptyState text="No submissions returned by the API." />
  return <div className="table-wrap"><table><thead><tr><th>Verdict</th><th>Language</th><th>Runtime</th><th>Submitted</th></tr></thead><tbody>{submissions.map((submission) => <tr key={submission.id}><td><Verdict value={submission.verdict} /></td><td>{submission.language}</td><td>{submission.execution_time_ms ?? '-'} ms</td><td>{new Date(submission.submitted_at).toLocaleString()}</td></tr>)}</tbody></table></div>
}

function BattleList({ battles, endingBattleId, onEndBattle }: { battles: Battle[]; endingBattleId?: string; onEndBattle?: (battle: Battle) => void }) {
  if (!battles.length) return <EmptyState text="No battle history returned by the API." />
  return (
    <div className="card-list">
      {battles.map((battle) => {
        const canEnd = isEndableBattle(battle)
        const isEnding = endingBattleId === battle.id
        return (
          <article className="mini-card horizontal" key={battle.id}>
            <div>
              <strong>{battle.problem_title}</strong>
              <span>{battle.host_username} vs {battle.opponent_username ?? 'open slot'}</span>
              <p>{battle.status} {battle.winner_username ? `• winner: ${battle.winner_username}` : ''}</p>
            </div>
            <div className="row-actions">
              {canEnd && onEndBattle && (
                <button className="ghost-button" disabled={isEnding} onClick={() => onEndBattle(battle)} type="button">
                  <X size={16} /> {isEnding ? 'Ending...' : 'End'}
                </button>
              )}
              <Link className="ghost-button" to={`/battles/${battle.id}`}>Open</Link>
            </div>
          </article>
        )
      })}
    </div>
  )
}

function isEndableBattle(battle: Battle) {
  return ['pending', 'active'].includes(battle.status.toLowerCase())
}

function ProblemSpec({ problem, compact }: { problem: ProblemDetail; compact?: boolean }) {
  return <div className="problem-spec"><div className="spec-header"><Difficulty value={problem.difficulty} />{problem.tags.map((tag) => <span className="tag" key={tag.id}>{tag.name}</span>)}</div><p>{problem.description}</p>{!compact && <><h3>Input</h3><p>{problem.input_format}</p><h3>Output</h3><p>{problem.output_format}</p><h3>Constraints</h3><pre>{problem.constraints}</pre><h3>Samples</h3>{problem.test_cases.map((test) => <div className="sample" key={test.id}><pre>{test.input}</pre><pre>{test.expected_output}</pre></div>)}</>}</div>
}

function Difficulty({ value }: { value: string }) {
  return <span className={`difficulty ${value.toLowerCase()}`}>{titleCase(value)}</span>
}

function Verdict({ value }: { value: string }) {
  return <span className={`verdict ${value.toLowerCase().replaceAll(' ', '-')}`}>{value}</span>
}

function DifficultyBars({ data }: { data?: { easy_solved: number; medium_solved: number; hard_solved: number; easy_total: number; medium_total: number; hard_total: number } }) {
  const rows = [
    { name: 'Easy', solved: data?.easy_solved ?? 0, total: data?.easy_total ?? 0 },
    { name: 'Medium', solved: data?.medium_solved ?? 0, total: data?.medium_total ?? 0 },
    { name: 'Hard', solved: data?.hard_solved ?? 0, total: data?.hard_total ?? 0 },
  ]
  return <div className="bar-stack">{rows.map((row) => <div key={row.name}><span>{row.name}</span><div><i style={{ width: `${row.total ? (row.solved / row.total) * 100 : 0}%` }} /></div><strong>{row.solved}/{row.total}</strong></div>)}</div>
}

function BattleTelemetry({ battle }: { battle: Battle }) {
  const items: Array<[string, React.ReactNode, React.ReactNode]> = [
    ['Status', battle.status.charAt(0).toUpperCase() + battle.status.slice(1), <Activity size={20} />],
    ['Duration', `${Math.round(battle.duration_seconds / 60)} min`, <Gauge size={20} />],
    ['Host', battle.host_username, <Users size={20} />],
    ['Opponent', battle.opponent_username ?? 'Pending', <Swords size={20} />],
  ]
  if (battle.status === 'finished') {
    items.push(['Winner', battle.winner_username ? `🏆 ${battle.winner_username}` : 'Draw', <Medal size={20} />])
  }
  return <div className="telemetry"><MetricGrid items={items} /></div>
}

function TextInput({ label, type = 'text', registration, error }: { label: string; type?: string; registration: object; error?: string }) {
  return <label className="field"><span>{label}</span><input type={type} {...registration} />{error && <small>{error}</small>}</label>
}

function ChartBox({ children }: { children: React.ReactNode }) {
  return <div className="chart-box">{children}</div>
}

function EmptyState({ text }: { text: string }) {
  return <p className="empty-state">{text}</p>
}

function Skeleton() {
  return <div className="skeleton"><span /><span /><span /></div>
}

function FullPageLoader() {
  return <main className="auth-page blueprint-bg"><div className="loader">Loading CodeClash...</div></main>
}

class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean }> {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) return <main className="auth-page blueprint-bg"><div className="auth-card"><h1>System fault</h1><p>Refresh the page to restart the frontend runtime.</p></div></main>
    return this.props.children
  }
}

const tooltipStyle = {
  background: '#151515',
  border: '1px solid #333',
  borderRadius: 6,
  color: '#f4f4f4',
}

function titleCase(value: string) {
  return value ? value[0].toUpperCase() + value.slice(1).toLowerCase() : value
}

export default App
