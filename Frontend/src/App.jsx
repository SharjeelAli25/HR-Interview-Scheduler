import React, { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export default function App() {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState([])
  const [interviews, setInterviews] = useState([])
  const [input, setInput] = useState('')
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.addEventListener('open', () => {
      setConnected(true)
      setMessages(m => [...m, { sender: 'system', text: 'Connected to server' }])
    })

    ws.addEventListener('message', (ev) => {
      try {
        const data = JSON.parse(ev.data)
        setMessages(m => [...m, { sender: data.sender || 'agent', text: data.text }])
        if (data.interviews) setInterviews(data.interviews)

        // If server returned a single interview (read_interview), show details in an alert
        if (data.sender === 'server' && data.action === 'read_interview') {
          try {
            const parsed = typeof data.text === 'string' ? JSON.parse(data.text) : data.text
            if (parsed && parsed.interview) {
              const iv = parsed.interview
              alert(`Interview ${iv.id}\nTitle: ${iv.title}\nDescription: ${iv.description}\nScheduled: ${iv.scheduled_date || 'N/A'}\nCreated: ${iv.created_at}`)
            }
          } catch (err) { /* ignore parse errors */ }
        }

      } catch (e) {
        setMessages(m => [...m, { sender: 'agent', text: ev.data }])
      }
    })

    ws.addEventListener('close', () => {
      setConnected(false)
      setMessages(m => [...m, { sender: 'system', text: 'Disconnected from server' }])
    })

    ws.addEventListener('error', (e) => {
      setMessages(m => [...m, { sender: 'system', text: 'WebSocket error' }])
    })

    return () => ws.close()
  }, [])

  function sendMessage() {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    const payload = { text: input }
    wsRef.current.send(JSON.stringify(payload))
    setMessages(m => [...m, { sender: 'user', text: input }])
    setInput('')
  }

  function sendAction(action, params = {}) {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    const payload = { action, params }
    wsRef.current.send(JSON.stringify(payload))
  }

  return (
    <div style={{padding: 24, color: '#111', width: 800, margin: '32px auto', background: 'white', borderRadius: 8}}>
      <h1>AI HR Interview Scheduler</h1>
      <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>

      <div style={{display: 'flex', gap: 16}}>
        <div style={{flex: 1}}>
          <div style={{height: 400, overflow: 'auto', border: '1px solid #eee', padding: 12}}>
            {messages.map((m, i) => (
              <div key={i} style={{marginBottom: 8}}>
                <strong>{m.sender}:</strong> {m.text}
              </div>
            ))}
          </div>

          <div style={{display: 'flex', gap: 8, marginTop: 8}}>
            <input value={input} onChange={e => setInput(e.target.value)} style={{flex: 1, padding: 8}} />
            <button onClick={sendMessage} style={{padding: '8px 12px'}}>Send</button>
          </div>
        </div>

        <div style={{width: 240}}>
          <h3>Interviews</h3>
          <ul>
            {interviews.length === 0 && <li>No interviews</li>}
            {interviews.map((iv) => (
              <li key={iv.id || Math.random()} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap:8}}>
                <span style={{flex:1}}>
                  <strong>{iv.title}</strong>
                  <div style={{fontSize:12}}>{iv.description || '—'}</div>
                  <div style={{fontSize:12, color:'#666'}}>Scheduled: {iv.scheduled_date || '—'}</div>
                </span>
                <span>
                  <button onClick={() => sendAction('read_interview', {interview_id: iv.id})}>View</button>
                  <button onClick={() => {
                    const newDate = prompt('Enter new scheduled date (e.g. 2025-12-25):', iv.scheduled_date || '')
                    if (newDate !== null) {
                      sendAction('update_interview', {interview_id: iv.id, scheduled_date: newDate})
                    }
                  }} style={{marginLeft:8}}>Edit</button>
                  <button onClick={() => sendAction('delete_interview', {interview_id: iv.id})} style={{marginLeft:8}}>Delete</button>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p style={{marginTop: 12}}><small>WS: {WS_URL}</small></p>
    </div>
  )
}
