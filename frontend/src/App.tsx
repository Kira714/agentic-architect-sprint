import { useState, useEffect, useRef } from 'react';
import { api, CreateProtocolRequest } from './api';
import { FoundryState, StateUpdate, AgentNote } from './types';
import ChatMessage from './components/ChatMessage';
import './App.css';

export interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'system' | 'draft' | 'review' | 'thinking' | 'response';
  agent?: string;
  content: string;
  timestamp: string;
  metadata?: any;
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [currentState, setCurrentState] = useState<FoundryState | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastNodeRef = useRef<string>('');
  const shownNoteIdsRef = useRef<Set<string>>(new Set());
  const shownReviewIdsRef = useRef<Set<string>>(new Set());
  const lastDraftVersionRef = useRef<number>(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (message: Omit<ChatMessage, 'id'>) => {
    setMessages(prev => [...prev, { ...message, id: Date.now().toString() + Math.random() }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput('');
    setIsStreaming(true);
    
    // Reset tracking refs for new conversation
    shownNoteIdsRef.current.clear();
    shownReviewIdsRef.current.clear();
    lastDraftVersionRef.current = 0;
    lastNodeRef.current = '';

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    });

    try {
      const request: CreateProtocolRequest = {
        user_query: userMessage,
        max_iterations: 10,
      };

      const response = await api.createProtocol(request);
      const newThreadId = response.thread_id;
      setThreadId(newThreadId);

      // Start streaming
      const eventSource = new EventSource(
        `/api/protocols/${newThreadId}/stream`
      );
      eventSourceRef.current = eventSource;

      console.log('[FRONTEND] EventSource created, connecting to stream...');

      // Handle thinking events - these come with event type "thinking"
      eventSource.addEventListener('thinking', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] Thinking event received:', data);
          
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.type === 'thinking' && lastMessage.metadata?.intent === data.intent) {
              // Update existing thinking message
              return prev.map((msg, idx) => 
                idx === prev.length - 1 
                  ? { ...msg, content: data.content }
                  : msg
              );
            } else {
              // Create new thinking message
              return [...prev, {
                id: Date.now().toString() + Math.random(),
                type: 'thinking',
                agent: data.agent || 'System',
                content: data.content,
                timestamp: data.timestamp || new Date().toISOString(),
                metadata: { intent: data.intent }
              }];
            }
          });
        } catch (err) {
          console.error('[FRONTEND] Error parsing thinking event:', err);
        }
      });

      // Handle response events
      eventSource.addEventListener('response', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] Response event received:', data);
          
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.type === 'response') {
              // Update existing response message
              return prev.map((msg, idx) => 
                idx === prev.length - 1 
                  ? { ...msg, content: data.content }
                  : msg
              );
            } else {
              // Create new response message
              return [...prev, {
                id: Date.now().toString() + Math.random(),
                type: 'response',
                content: data.content,
                timestamp: data.timestamp || new Date().toISOString(),
              }];
            }
          });
          
          if (data.is_complete) {
            console.log('[FRONTEND] Response complete, closing stream');
            setIsStreaming(false);
            setTimeout(() => {
              eventSource.close();
            }, 100);
          }
        } catch (err) {
          console.error('[FRONTEND] Error parsing response event:', err);
        }
      });

      // Handle state_update events
      eventSource.addEventListener('state_update', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] State update event received:', data);
          
          const update: StateUpdate = {
            event: 'state_update',
            node: data.node,
            state: data.state,
            timestamp: data.timestamp || new Date().toISOString()
          };
          if (update.state) {
            handleStateUpdate(update);
          }
        } catch (err) {
          console.error('[FRONTEND] Error parsing state_update event:', err);
        }
      });

      // Handle halted events
      eventSource.addEventListener('halted', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] Halted event received:', data);
          
          // If halted due to questions, show them to the user
          if (data.awaiting_user_response && data.questions && data.questions.length > 0) {
            addMessage({
              type: 'system',
              content: `I need some additional information to create the best exercise plan for you. Please answer these questions:\n\n${data.questions.map((q: string, i: number) => `${i + 1}. ${q}`).join('\n\n')}`,
              timestamp: new Date().toISOString(),
            });
          }
          
          handleStateUpdate({ 
            event: 'halted',
            state: data.state, 
            node: 'halt', 
            timestamp: data.timestamp || new Date().toISOString() 
          });
          setIsStreaming(false);
          eventSource.close();
        } catch (err) {
          console.error('[FRONTEND] Error parsing halted event:', err);
        }
      });

      // Handle completed events
      eventSource.addEventListener('completed', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] Completed event received:', data);
          
          handleStateUpdate({ 
            event: 'completed',
            state: data.state, 
            node: 'complete', 
            timestamp: data.timestamp || new Date().toISOString() 
          });
          setIsStreaming(false);
          eventSource.close();
        } catch (err) {
          console.error('[FRONTEND] Error parsing completed event:', err);
        }
      });

      // Handle error events
      eventSource.addEventListener('error', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.error('[FRONTEND] Error event received:', data);
          
          addMessage({
            type: 'system',
            content: `Error: ${data.error || 'Unknown error'}`,
            timestamp: new Date().toISOString(),
          });
          setIsStreaming(false);
          eventSource.close();
        } catch (err) {
          console.error('[FRONTEND] Error parsing error event:', err);
        }
      });

      // Fallback: handle default message events (for events without specific type)
      eventSource.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[FRONTEND] Default message event received:', data);
          
          // Try to handle based on data.event field
          if (data.event === 'thinking') {
            const thinkingEvent = new MessageEvent('thinking', { data: event.data });
            eventSource.dispatchEvent(thinkingEvent);
          } else if (data.event === 'response') {
            const responseEvent = new MessageEvent('response', { data: event.data });
            eventSource.dispatchEvent(responseEvent);
          } else if (data.event === 'state_update') {
            const stateEvent = new MessageEvent('state_update', { data: event.data });
            eventSource.dispatchEvent(stateEvent);
          }
        } catch (err) {
          console.error('[FRONTEND] Error parsing default message event:', err);
        }
      };

      // Handle connection errors
      eventSource.onerror = (err) => {
        console.error('[FRONTEND] SSE connection error:', err, 'readyState:', eventSource.readyState);
        // Only show error if connection is actually closed (readyState 2 = CLOSED)
        if (eventSource.readyState === EventSource.CLOSED && isStreaming) {
          addMessage({
            type: 'system',
            content: `Connection error. Please try again.`,
            timestamp: new Date().toISOString(),
          });
          setIsStreaming(false);
          eventSource.close();
        }
        // If readyState is CONNECTING (0) or OPEN (1), just log - connection might recover
      };

      // Log when connection opens
      eventSource.onopen = () => {
        console.log('[FRONTEND] SSE connection opened');
      };
    } catch (err: any) {
      addMessage({
        type: 'system',
        content: `Failed to start: ${err.message}`,
        timestamp: new Date().toISOString(),
      });
      setIsStreaming(false);
    }
  };

  const handleStateUpdate = (update: StateUpdate) => {
    if (!update.state) {
      console.warn('State update missing state:', update);
      return;
    }
    
    const state = update.state;
    setCurrentState(state);
    
    const node = update.node;
    const currentAgent = state.current_agent;

    // Show agent activity when node changes
    if (node && node !== lastNodeRef.current) {
      lastNodeRef.current = node;
      
      const agentNames: Record<string, string> = {
        supervisor: 'Supervisor',
        draftsman: 'Draftsman',
        safety_guardian: 'Safety Guardian',
        clinical_critic: 'Clinical Critic',
      };

      const agentName = agentNames[node] || node;
      
      // Show agent thinking (all as thinking messages)
      if (node === 'supervisor') {
        addMessage({
          type: 'thinking',
          agent: 'Supervisor',
          content: `Thinking: Analyzing workflow state... Deciding next action.`,
          timestamp: update.timestamp,
        });
      } else if (node === 'draftsman') {
        addMessage({
          type: 'thinking',
          agent: 'Draftsman',
          content: `Thinking: Creating CBT exercise draft...`,
          timestamp: update.timestamp,
        });
      } else if (node === 'safety_guardian') {
        addMessage({
          type: 'thinking',
          agent: 'Safety Guardian',
          content: `Thinking: Reviewing draft for safety concerns...`,
          timestamp: update.timestamp,
        });
      } else if (node === 'clinical_critic') {
        addMessage({
          type: 'thinking',
          agent: 'Clinical Critic',
          content: `Thinking: Evaluating clinical quality and empathy...`,
          timestamp: update.timestamp,
        });
      } else if (node === 'information_gatherer') {
        addMessage({
          type: 'thinking',
          agent: 'Information Gatherer',
          content: `Thinking: Analyzing user request to identify needed information...`,
          timestamp: update.timestamp,
        });
      } else if (node === 'debate_moderator') {
        addMessage({
          type: 'thinking',
          agent: 'Debate Moderator',
          content: `Thinking: Facilitating internal debate to refine the exercise plan...`,
          timestamp: update.timestamp,
        });
      }
    }

    // Show new agent notes (avoid duplicates)
    // Note: Thinking messages are already streamed by backend, so we only show non-thinking notes here
    if (state.agent_notes && state.agent_notes.length > 0) {
      const agentNames: Record<string, string> = {
        supervisor: 'Supervisor',
        draftsman: 'Draftsman',
        safety_guardian: 'Safety Guardian',
        clinical_critic: 'Clinical Critic',
      };
      
      // Show all new notes that haven't been shown yet
      // Skip notes that start with "Thinking:" as those are streamed separately
      state.agent_notes.forEach((note) => {
        const noteId = `${note.timestamp}-${note.message.substring(0, 50)}`;
        if (!shownNoteIdsRef.current.has(noteId)) {
          shownNoteIdsRef.current.add(noteId);
          
          // Only show non-thinking notes here (thinking is streamed separately)
          const message = note.message || '';
          const isThinking = message.toLowerCase().includes('thinking:') || message.toLowerCase().startsWith('thinking');
          
          if (!isThinking) {
            addMessage({
              type: 'agent',
              agent: agentNames[note.agent] || note.agent,
              content: note.message,
              timestamp: note.timestamp,
              metadata: { ...note.context, note_id: noteId },
            });
          }
        }
      });
    }

            // Show draft updates (only when version changes) - this is the FINAL output, not thinking
            if (state.current_draft && state.current_version !== lastDraftVersionRef.current) {
              lastDraftVersionRef.current = state.current_version;
              
              // Remove old draft messages
              setMessages(prev => prev.filter(m => m.type !== 'draft'));
              
              // Add draft as final output (not thinking)
              addMessage({
                type: 'draft',
                content: state.current_draft,
                timestamp: state.last_updated,
                metadata: { version: state.current_version, draft_id: `draft-${state.current_version}` },
              });
            }

    // Show safety review (avoid duplicates)
    if (state.safety_review) {
      const review = state.safety_review;
      const reviewId = `safety-${review.reviewed_at || state.last_updated}`;
      
      if (!shownReviewIdsRef.current.has(reviewId)) {
        shownReviewIdsRef.current.add(reviewId);
        
        if (review.status === 'flagged' || review.status === 'critical') {
          addMessage({
            type: 'review',
            agent: 'Safety Guardian',
            content: `Safety Review Results:\nStatus: ${review.status.toUpperCase()}\n\nConcerns:\n${review.concerns.map((c, i) => `${i + 1}. ${c}`).join('\n')}\n\nRecommendations:\n${review.recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')}`,
            timestamp: review.reviewed_at || new Date().toISOString(),
            metadata: { review_id: reviewId },
          });
        } else if (review.status === 'passed') {
          addMessage({
            type: 'review',
            agent: 'Safety Guardian',
            content: `Safety Review: PASSED\nNo safety concerns identified. Draft is safe for clinical use.`,
            timestamp: review.reviewed_at || new Date().toISOString(),
            metadata: { review_id: reviewId },
          });
        }
      }
    }

    // Show clinical review (avoid duplicates)
    if (state.clinical_review) {
      const review = state.clinical_review;
      const reviewId = `clinical-${review.reviewed_at || state.last_updated}`;
      
      if (!shownReviewIdsRef.current.has(reviewId)) {
        shownReviewIdsRef.current.add(reviewId);
        const avgScore = (review.empathy_score + review.tone_score + review.structure_score) / 3;
        
        addMessage({
          type: 'review',
          agent: 'Clinical Critic',
          content: `Clinical Review Results:\nStatus: ${review.status.toUpperCase()}\n\nQuality Scores:\n• Empathy: ${review.empathy_score.toFixed(1)}/10\n• Tone: ${review.tone_score.toFixed(1)}/10\n• Structure: ${review.structure_score.toFixed(1)}/10\n• Average: ${avgScore.toFixed(1)}/10\n\nFeedback:\n${review.feedback.map((f, i) => `${i + 1}. ${f}`).join('\n')}`,
          timestamp: review.reviewed_at || new Date().toISOString(),
          metadata: { review_id: reviewId },
        });
      }
    }

    // Show halt message - differentiate between awaiting questions vs awaiting draft approval
    if (state.is_halted || state.awaiting_human_approval || state.awaiting_user_response) {
      if (state.awaiting_user_response && state.questions_for_user && state.questions_for_user.length > 0) {
        // Already shown in halted event handler, don't duplicate
      } else if (state.current_draft) {
        // Has a draft, awaiting approval
        addMessage({
          type: 'system',
          content: `Workflow paused for human review. Please review the draft above and approve to continue.`,
          timestamp: new Date().toISOString(),
        });
      } else {
        // Halted but no draft yet - might be an error
        addMessage({
          type: 'system',
          content: `Workflow paused. Waiting for next step...`,
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Show completion
    if (state.final_protocol) {
      addMessage({
        type: 'system',
        content: `Protocol generation completed!`,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const handleApprove = async () => {
    if (!threadId || !currentState) return;

    try {
      await api.approveProtocol(threadId, {
        edited_draft: currentState.current_draft || undefined,
        feedback: undefined,
        user_specifics: currentState.user_specifics || undefined,
      });

      addMessage({
        type: 'system',
        content: `Protocol approved and finalized!`,
        timestamp: new Date().toISOString(),
      });

      setIsStreaming(false);
    } catch (err: any) {
      addMessage({
        type: 'system',
        content: `Error: ${err.message}`,
        timestamp: new Date().toISOString(),
      });
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Cerina Protocol Foundry</h1>
          <p>Autonomous CBT Exercise Design System</p>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>Ask me to create a CBT exercise protocol.</p>
              <p className="hint">Example: "Create an exposure hierarchy for agoraphobia"</p>
            </div>
          )}
          
          {messages.map((message, index) => (
            <ChatMessage 
              key={message.id} 
              message={message}
              isStreaming={isStreaming && index === messages.length - 1 && (message.type === 'thinking' || message.type === 'response' || message.type === 'agent')}
            />
          ))}
          
          {isStreaming && messages.length > 0 && !['thinking', 'response', 'agent'].includes(messages[messages.length - 1]?.type || '') && (
            <div className="message assistant-message">
              <div className="message-avatar">
                <div className="avatar-circle assistant-avatar">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 0C4.47715 0 0 4.47715 0 10C0 15.5228 4.47715 20 10 20C15.5228 20 20 15.5228 20 10C20 4.47715 15.5228 0 10 0ZM10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2C14.4183 2 18 5.58172 18 10C18 14.4183 14.4183 18 10 18Z" fill="currentColor"/>
                  </svg>
                </div>
              </div>
              <div className="message-content-wrapper">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {currentState?.awaiting_human_approval && currentState?.current_draft && (
          <div className="approval-bar">
            <button onClick={handleApprove} className="approve-button">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '8px' }}>
                <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Approve & Finalize
            </button>
          </div>
        )}
        
        {currentState?.awaiting_user_response && currentState?.questions_for_user && currentState.questions_for_user.length > 0 && (
          <div className="questions-bar">
            <p className="questions-prompt">I need some additional information to create the best exercise plan for you. Please answer these questions:</p>
            <div className="questions-list">
              {currentState.questions_for_user.map((q: string, i: number) => (
                <div key={i} className="question-item">
                  <p className="question-text">{i + 1}. {q}</p>
                </div>
              ))}
            </div>
            <p className="questions-note">You can continue the conversation by answering these questions naturally in your next message.</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="chat-input-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask me to create a CBT exercise protocol..."
            rows={1}
            className="chat-input"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="send-button"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
