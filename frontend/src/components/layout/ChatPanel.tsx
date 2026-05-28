import { useState, useRef, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { Send, Bot, Trash2, ChevronRight, Loader2, Wrench } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChatStore } from '../../stores/chatStore'
import api from '../../api/client'
import { clsx } from 'clsx'

function getPageName(pathname: string): string {
  const parts = pathname.split('/')
  return parts[parts.length - 1] || 'dashboard'
}

export default function ChatPanel() {
  const location = useLocation()
  const page = getPageName(location.pathname)
  const [input, setInput] = useState('')
  const [toolActivity, setToolActivity] = useState<string | null>(null)
  const { history, isStreaming, addMessage, setStreaming, clearHistory, updateLastAssistant } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: suggested } = useQuery({
    queryKey: ['suggested-prompts', page],
    queryFn: () => api.get(`/chat/suggested-prompts/${page}`).then((r) => r.data as string[]),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, toolActivity])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return
    const userMsg = text.trim()
    setInput('')
    addMessage({ role: 'user', content: userMsg })
    setStreaming(true)
    setToolActivity(null)

    let assistantContent = ''

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: userMsg,
          history: history.slice(-20),
          page_context: page,
        }),
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'text') {
              assistantContent += event.content
              updateLastAssistant(assistantContent)
              setToolActivity(null)
            } else if (event.type === 'tool_call') {
              setToolActivity(`Querying: ${event.tool.replace(/_/g, ' ')}…`)
            } else if (event.type === 'tool_result') {
              setToolActivity(null)
            } else if (event.type === 'done') {
              setToolActivity(null)
            } else if (event.type === 'error') {
              updateLastAssistant(`Error: ${event.content}`)
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      updateLastAssistant('Sorry, I encountered an error. Please try again.')
    } finally {
      setStreaming(false)
      setToolActivity(null)
    }
  }, [history, isStreaming, page, addMessage, setStreaming, updateLastAssistant])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="w-80 bg-navy-800 border-l border-navy-500 flex flex-col shrink-0">
      {/* Header */}
      <div className="px-3 py-3 border-b border-navy-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-steel-400/20 border border-steel-400/40 flex items-center justify-center">
            <Bot size={14} className="text-steel-400" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">AI Assistant</div>
            <div className="text-xs text-steel-300">Claude Sonnet 4.6</div>
          </div>
        </div>
        <button
          onClick={clearHistory}
          className="p-1.5 hover:bg-navy-600 rounded text-steel-300 hover:text-white transition-colors"
          title="Clear chat"
        >
          <Trash2 size={13} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {history.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-steel-300 leading-relaxed">
              I'm monitoring the facility. Ask me anything about assets, alerts, or operations.
            </p>
            {suggested && suggested.length > 0 && (
              <div className="space-y-1.5 mt-3">
                <div className="text-xs text-steel-300/70 uppercase tracking-wider mb-1">Suggested</div>
                {suggested.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    className="w-full text-left text-xs text-steel-200 bg-navy-700 hover:bg-navy-600 border border-navy-500 rounded-md px-2.5 py-1.5 transition-colors flex items-center gap-1.5 group"
                  >
                    <ChevronRight size={11} className="text-steel-400 group-hover:text-steel-300 shrink-0" />
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {history.map((msg, i) => (
          <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div
              className={clsx(
                'max-w-[90%] text-xs rounded-lg px-3 py-2 leading-relaxed',
                msg.role === 'user'
                  ? 'bg-steel-400 text-white rounded-br-sm'
                  : 'bg-navy-700 text-steel-100 border border-navy-500 rounded-bl-sm'
              )}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-invert prose-xs max-w-none [&_p]:mb-1.5 [&_ul]:mb-1.5 [&_ol]:mb-1.5 [&_h3]:text-steel-300 [&_h3]:text-xs [&_h3]:font-semibold [&_strong]:text-white [&_code]:bg-navy-900 [&_code]:px-1 [&_code]:rounded [&_table]:text-xs">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {/* Tool activity indicator */}
        {toolActivity && (
          <div className="flex items-center gap-2 text-xs text-steel-300 bg-navy-700/50 border border-navy-500 rounded-lg px-3 py-2">
            <Wrench size={11} className="text-steel-400 shrink-0 animate-pulse" />
            <span>{toolActivity}</span>
          </div>
        )}

        {/* Streaming indicator */}
        {isStreaming && !toolActivity && (
          <div className="flex items-center gap-2 text-xs text-steel-300">
            <Loader2 size={11} className="animate-spin text-steel-400" />
            <span>Thinking…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-navy-500">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything…"
            rows={2}
            disabled={isStreaming}
            className="flex-1 resize-none input text-xs py-2 leading-relaxed"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={isStreaming || !input.trim()}
            className="p-2 bg-steel-400 hover:bg-steel-300 disabled:opacity-40 disabled:cursor-not-allowed rounded-md text-white transition-colors shrink-0"
          >
            {isStreaming ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          </button>
        </div>
        <p className="text-xs text-steel-300/50 mt-1.5">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  )
}
