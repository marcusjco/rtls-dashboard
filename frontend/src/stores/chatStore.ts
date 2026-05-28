import { create } from 'zustand'
import type { ChatMessage } from '../types'

interface ChatState {
  history: ChatMessage[]
  isStreaming: boolean
  addMessage: (msg: ChatMessage) => void
  setStreaming: (v: boolean) => void
  clearHistory: () => void
  updateLastAssistant: (content: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  history: [],
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ history: [...s.history, msg] })),
  setStreaming: (v) => set({ isStreaming: v }),
  clearHistory: () => set({ history: [] }),
  updateLastAssistant: (content) =>
    set((s) => {
      const history = [...s.history]
      const last = history[history.length - 1]
      if (last?.role === 'assistant') {
        history[history.length - 1] = { ...last, content }
      } else {
        history.push({ role: 'assistant', content })
      }
      return { history }
    }),
}))
