import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './styles.css'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'cocktail_agent_token'
const REFRESH_TOKEN_KEY = 'cocktail_agent_refresh_token'
const USER_KEY = 'cocktail_agent_user'

const suggestions = [
  { label: 'Clásico', text: '¿Cómo preparo un Negroni equilibrado?' },
  { label: 'Ingredientes', text: '¿Cómo preparo un Mojito con ron, lima y hierbabuena?' },
  { label: 'Clásico', text: '¿Cómo preparo una Margarita clásica?' },
]

async function api(path, options = {}, token) {
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  let response
  try { response = await fetch(`${API_URL}${path}`, { ...options, headers }) } catch { throw new Error(`No se pudo conectar con la API en ${API_URL}. Inicia el backend en el puerto 8000.`) }
  if (response.status === 204) return null
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) { const error = new Error(payload.detail || 'No pudimos completar la solicitud.'); error.status = response.status; throw error }
  return payload
}

function saveSession(session, user) {
  localStorage.setItem(TOKEN_KEY, session.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

function clearSessionStorage() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function Icon({ name, size = 20 }) {
  const paths = {
    spark: <><path d="m12 2 1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5L12 2Z"/><path d="m19 16 .6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
    book: <><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22V4.5Z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    upload: <><path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M5 20h14"/></>,
    trash: <><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-5"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  async function submit(event) {
    event.preventDefault()
    setBusy(true); setNotice('')
    try {
      const result = await api(`/auth/${mode === 'login' ? 'login' : 'register'}`, { method: 'POST', body: JSON.stringify({ email, password }) })
      if (mode === 'register' && !result.session) {
        setNotice('Cuenta creada. Revisa tu correo para confirmar el acceso.')
        setMode('login')
      } else {
        const session = mode === 'login' ? result : result.session
        saveSession(session, result.user)
        onAuthenticated(session.access_token, result.user)
      }
    } catch (error) { setNotice(error.message) } finally { setBusy(false) }
  }

  return <main className="auth-shell">
    <div className="auth-orbit orbit-one" /><div className="auth-orbit orbit-two" />
    <section className="auth-panel glass-card">
      <div className="brand-mark"><span><Icon name="spark" size={22} /></span><strong>pour<span>·</span>over</strong></div>
      <div className="auth-copy"><h1>Tu próxima<br />mezcla empieza aquí.</h1><p>Un copiloto para explorar, comparar y crear cócteles con contexto real.</p></div>
      <form onSubmit={submit} className="auth-form">
        <label>Correo electrónico<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="tu@email.com" required /></label>
        <label>Contraseña<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength="6" required /></label>
        {notice && <div className="notice">{notice}</div>}
        <button className="primary-button full" disabled={busy}>{busy ? 'Conectando…' : mode === 'login' ? 'Entrar al laboratorio' : 'Crear mi cuenta'} <Icon name="arrow" size={18} /></button>
      </form>
      <p className="auth-switch">{mode === 'login' ? '¿Primera vez por aquí?' : '¿Ya tienes una cuenta?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setNotice('') }}>{mode === 'login' ? 'Crear cuenta' : 'Iniciar sesión'}</button></p>
    </section>
    <aside className="auth-aside"><div className="cocktail-illustration"><div className="glass-shape"><span className="liquid" /><span className="olive" /></div><div className="stem" /><div className="base" /></div></aside>
  </main>
}

function Sidebar({ user, conversations, activeId, onSelect, onNew, onDocs, onLogout, docsOpen, onClose }) {
  return <aside className="sidebar">
    <div className="sidebar-top"><div className="brand-mark"><span><Icon name="spark" size={20} /></span><strong>pour<span>·</span>over</strong></div><button className="icon-button mobile-close" onClick={onClose}><Icon name="close" /></button></div>
    <button className="new-chat" onClick={onNew}><Icon name="plus" size={18} /> Nueva conversación</button>
    <div className="side-section"><p className="side-label">RECENT JOURNEYS</p>{conversations.length ? conversations.map(item => <button className={`conversation-link ${activeId === item.id ? 'active' : ''}`} key={item.id} onClick={() => onSelect(item.id)}><span className="chat-dot" />{item.title || 'Nueva exploración'}</button>) : <p className="empty-side">Tus exploraciones aparecerán aquí.</p>}</div>
    <div className="sidebar-bottom"><button className={`library-link ${docsOpen ? 'active' : ''}`} onClick={onDocs}><Icon name="book" size={18} /><span>Mi biblioteca</span><b>•</b></button><div className="profile"><div className="avatar">{(user?.email || 'A').slice(0, 1).toUpperCase()}</div><div><strong>{user?.email?.split('@')[0] || 'Mixólogo'}</strong><small>Cuenta personal</small></div><button className="icon-button" onClick={onLogout} title="Cerrar sesión"><Icon name="logout" size={17} /></button></div></div>
  </aside>
}

function Composer({ onSubmit, busy }) {
  const [value, setValue] = useState('')
  const textarea = useRef(null)
  function submit(event) { event.preventDefault(); if (value.trim() && !busy) { onSubmit(value.trim()); setValue(''); } }
  return <form className="composer" onSubmit={submit}><textarea ref={textarea} value={value} onChange={e => setValue(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(e) } }} placeholder="Pregunta por un cóctel, ingrediente o técnica…" rows="1" /><div className="composer-footer"><span>↵ para enviar · shift + ↵ nueva línea</span><button className="send-button" disabled={!value.trim() || busy} aria-label="Enviar pregunta"><Icon name="send" size={18} /></button></div></form>
}

function SourceCard({ source, index }) {
  const sourceUrl = typeof source.source_uri === 'string' && source.source_uri.startsWith('https://') ? source.source_uri : null
  return <a className="source-card" href={sourceUrl || undefined} target="_blank" rel="noopener noreferrer"><span className="source-number">0{index + 1}</span><span className="source-info"><strong>{source.title || 'Fuente de conocimiento'}</strong><small>{source.source_type === 'cocktaildb' ? 'TheCocktailDB' : 'Documento propio'} · relevancia {Math.round((source.similarity || 0) * 100)}%</small></span><Icon name="arrow" size={16} /></a>
}

function Message({ message }) {
  const assistant = message.role === 'assistant'
  const [imageFailed, setImageFailed] = useState(false)
  const imageUrl = assistant ? message.sources?.find(source => typeof source.image_url === 'string' && source.image_url.startsWith('https://'))?.image_url : null
  const showImage = Boolean(imageUrl && !imageFailed)
  return <article className={`message ${assistant ? 'assistant' : 'user'} ${showImage ? 'with-image' : ''}`}><div className="message-avatar">{assistant ? <Icon name="spark" size={16} /> : 'TÚ'}</div><div className="message-body"><div className="message-meta"><strong>{assistant ? 'Pourover' : 'Tú'}</strong><time>{message.time || 'ahora'}</time></div><div className="message-text">{assistant ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown> : message.content}</div>{assistant && message.sources?.length > 0 && <div className="sources"><p className="eyebrow">FUENTES CONSULTADAS</p>{message.sources.map((source, index) => <SourceCard key={`${source.chunk_id || index}`} source={source} index={index} />)}</div>}{assistant && message.context_sufficient === false && <div className="context-note"><span>i</span> Contexto insuficiente · prueba con una pregunta más cercana a tus documentos.</div>}</div>{showImage && <figure className="message-image"><img src={imageUrl} alt={message.sources.find(source => source.image_url === imageUrl)?.title || 'Cóctel identificado'} onError={() => setImageFailed(true)} /><figcaption><span>COCKTAIL IDENTIFICADO</span><strong>{message.sources.find(source => source.image_url === imageUrl)?.title || 'Cóctel'}</strong></figcaption></figure>}</article>
}

function Library({ documents, onUpload, onDelete, onClose }) {
  const input = useRef(null)
  const [uploading, setUploading] = useState(false)
  async function upload(event) { const file = event.target.files?.[0]; if (!file) return; setUploading(true); try { await onUpload(file) } finally { setUploading(false); event.target.value = '' } }
  return <aside className="library-panel glass-card"><div className="panel-heading"><div><p className="eyebrow">PRIVATE CORPUS</p><h2>Mi biblioteca</h2></div><button className="icon-button" onClick={onClose}><Icon name="close" /></button></div><p className="panel-description">Añade recetas, notas y referencias para que el agente las use como contexto.</p><input ref={input} type="file" accept=".pdf,.txt,.md,.markdown,.csv" hidden onChange={upload} /><button className="upload-button" onClick={() => input.current?.click()} disabled={uploading}><Icon name="upload" size={18} />{uploading ? 'Procesando archivo…' : 'Cargar documento'}</button><p className="file-hint">PDF, TXT, Markdown o CSV · máximo 10 MiB</p><div className="document-list">{documents.length ? documents.map(doc => <div className="document-row" key={doc.id}><div className={`file-icon ${doc.status}`}><Icon name="book" size={17} /></div><div className="document-info"><strong>{doc.title || doc.filename || 'Documento sin título'}</strong><small><span className={`status-dot ${doc.status}`} />{doc.status === 'ready' ? 'Listo para consultar' : doc.status === 'error' ? 'No se pudo procesar' : 'Procesando…'}</small></div>{doc.source_type === 'upload' && <button className="icon-button delete-button" onClick={() => onDelete(doc.id)} title="Eliminar documento"><Icon name="trash" size={16} /></button>}</div>) : <div className="empty-library"><Icon name="book" size={27} /><p>Aún no hay documentos propios.</p><small>Tu biblioteca empieza con una buena receta.</small></div>}</div></aside>
}

function App() {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [booting, setBooting] = useState(true)
  const [docsOpen, setDocsOpen] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)
  const [error, setError] = useState('')

  const refreshInFlight = useRef(null)

  const refreshSession = useCallback(() => {
    if (refreshInFlight.current) return refreshInFlight.current

    const request = (async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (!refreshToken) {
        clearSessionStorage()
        setBooting(false)
        return null
      }
      try {
        const session = await api('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) })
        saveSession(session, session.user)
        setToken(session.access_token)
        setUser(session.user)
        setBooting(false)
        return session.access_token
      } catch (error) {
        const invalidRefreshToken = [400, 401, 403].includes(error.status)
        if (invalidRefreshToken) {
          clearSessionStorage()
          setToken(null)
          setUser(null)
        } else {
          setError('No se pudo renovar la sesión. Conservamos la sesión local y reintentaremos automáticamente.')
        }
        setBooting(false)
        return null
      }
    })()

    refreshInFlight.current = request.finally(() => {
      if (refreshInFlight.current === request) refreshInFlight.current = null
    })
    return refreshInFlight.current
  }, [])

  useEffect(() => {
    refreshSession()
    const interval = window.setInterval(refreshSession, 5 * 60 * 1000)
    return () => window.clearInterval(interval)
  }, [refreshSession])

  const loadWorkspace = useCallback(async () => {
    if (!token) return
    try {
      const [conversationData, documentData] = await Promise.all([api('/conversations', {}, token), api('/documents', {}, token)])
      setConversations(conversationData.items || [])
      setDocuments(documentData.items || [])
    } catch (err) {
      if (err.status === 401) await refreshSession()
      else setError(err.message)
    } finally {
      setBooting(false)
    }
  }, [token, refreshSession])

  useEffect(() => { loadWorkspace() }, [loadWorkspace])

  async function selectConversation(id) { setActiveId(id); setMobileMenu(false); setError(''); try { const data = await api(`/conversations/${id}/messages`, {}, token); setMessages((data.items || []).map(item => ({ ...item, time: item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'ahora' }))) } catch (err) { setError(err.message) } }
  function newChat() { setActiveId(null); setMessages([]); setDocsOpen(false); setMobileMenu(false); setError('') }
  async function ask(question) { setLoading(true); setError(''); const userMessage = { role: 'user', content: question, time: 'ahora' }; setMessages(current => [...current, userMessage]); try { const result = await api('/chat/query', { method: 'POST', body: JSON.stringify({ question, conversation_id: activeId || undefined }) }, token); setActiveId(result.conversation_id); setMessages(current => [...current, { role: 'assistant', content: result.answer, sources: result.sources, context_sufficient: result.context_sufficient, time: 'ahora' }]); const data = await api('/conversations', {}, token); setConversations(data.items || []) } catch (err) { setError(err.message); setMessages(current => current.slice(0, -1)) } finally { setLoading(false) } }
  async function upload(file) { setError(''); const form = new FormData(); form.append('file', file); try { const result = await api('/documents', { method: 'POST', body: form }, token); setDocuments(current => [result.document, ...current]) } catch (err) { setError(err.message) } }
  async function deleteDocument(id) { try { await api(`/documents/${id}`, { method: 'DELETE' }, token); setDocuments(current => current.filter(doc => doc.id !== id)) } catch (err) { setError(err.message) } }
  async function handleLogout() { try { if (token) await api('/auth/logout', { method: 'POST' }, token) } catch { /* local session still gets cleared */ } finally { clearSessionStorage(); setToken(null); setUser(null) } }
  function onAuthenticated(nextToken, nextUser) { setToken(nextToken); setUser(nextUser); setBooting(true) }

  const hasConversation = messages.length > 0
  const greeting = useMemo(() => user?.email?.split('@')[0] || 'explorador', [user])
  if (!token) return <AuthScreen onAuthenticated={onAuthenticated} />
  if (booting) return <div className="loading-screen"><div className="loader-mark"><Icon name="spark" size={27} /></div><p>Preparando tu barra de exploración…</p></div>
  return <div className="app-shell"><div className={`mobile-overlay ${mobileMenu ? 'visible' : ''}`} onClick={() => setMobileMenu(false)} /><div className={mobileMenu ? 'sidebar-wrap open' : 'sidebar-wrap'}><Sidebar user={user} conversations={conversations} activeId={activeId} onSelect={selectConversation} onNew={newChat} onDocs={() => setDocsOpen(!docsOpen)} docsOpen={docsOpen} onLogout={handleLogout} onClose={() => setMobileMenu(false)} /></div><main className="workspace"><header className="topbar"><button className="icon-button menu-button" onClick={() => setMobileMenu(true)}><Icon name="menu" /></button><div className="breadcrumb"><span>Workspace</span><b>/</b><strong>{docsOpen ? 'Biblioteca' : activeId ? 'Conversación' : 'Nueva exploración'}</strong></div><div className="topbar-status"><span className="online-dot" /> Agente listo</div></header>{error && <div className="error-banner"><span>{error}</span><button onClick={() => setError('')}><Icon name="close" size={15} /></button></div>}{docsOpen ? <Library documents={documents} onUpload={upload} onDelete={deleteDocument} onClose={() => setDocsOpen(false)} /> : <section className={`chat-stage ${hasConversation ? 'has-messages' : ''}`}>{!hasConversation ? <div className="welcome"><div className="welcome-orb"><Icon name="spark" size={30} /></div><p className="eyebrow">BUENAS, {greeting.toUpperCase()}</p><h1>¿Qué vamos a<br /><em>mezclar</em> hoy?</h1><p className="welcome-subtitle">Pregúntame por recetas, técnicas o ingredientes.<br />Responderé sólo con lo que podemos respaldar.</p><div className="suggestion-grid">{suggestions.map(item => <button className="suggestion-card" key={item.label} onClick={() => ask(item.text)}><span>{item.label}</span><strong>{item.text}</strong><Icon name="arrow" size={16} /></button>)}</div></div> : <div className="message-list">{messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}{loading && <div className="typing"><span /><span /><span /> Pour over está pensando</div>}</div>}<div className="composer-wrap"><Composer onSubmit={ask} busy={loading} /><p className="disclaimer">Pourover puede equivocarse. Verifica siempre las proporciones antes de servir.</p></div></section>}</main></div>
}

export default App
