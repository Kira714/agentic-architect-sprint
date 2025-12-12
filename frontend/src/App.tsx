import { useState, useEffect, useRef } from 'react';
import { api, CreateProtocolRequest } from './api';
import { FoundryState, StateUpdate } from './types';
import ChatMessage from './components/ChatMessage';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
  const [editedDraft, setEditedDraft] = useState<string>('');
  const [showSourceEditor, setShowSourceEditor] = useState<boolean>(false);
  const [isApproved, setIsApproved] = useState<boolean>(false);
  const [showApprovalSection, setShowApprovalSection] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastNodeRef = useRef<string>('');
  const shownNoteIdsRef = useRef<Set<string>>(new Set());
  const shownReviewIdsRef = useRef<Set<string>>(new Set());
  const lastDraftVersionRef = useRef<number>(0);
  const hasAutoShownEditorRef = useRef<boolean>(false);
  const isUserStoppedRef = useRef<boolean>(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize edited draft when draft becomes available for approval
  useEffect(() => {
    if (currentState?.current_draft && (currentState?.is_halted || currentState?.awaiting_human_approval)) {
      // Only initialize if edited draft is empty (first time showing approval section)
      if (!editedDraft) {
        setEditedDraft(currentState.current_draft);
      }
    } else if (!currentState?.awaiting_human_approval && !currentState?.is_halted) {
      // Clear edited draft when approval section is no longer shown
      setEditedDraft('');
    }
  }, [currentState?.current_draft, currentState?.is_halted, currentState?.awaiting_human_approval]);

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
    hasAutoShownEditorRef.current = false;
    
    // Reset approval states
    setIsApproved(false);
    setShowApprovalSection(false);
    setEditedDraft('');
    isUserStoppedRef.current = false;

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
            isUserStoppedRef.current = false; // Reset for next stream
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
          
          handleStateUpdate({ 
            state: data.state, 
            node: 'halt', 
            timestamp: data.timestamp || new Date().toISOString() 
          });
          setIsStreaming(false);
          isUserStoppedRef.current = false; // Reset for next stream
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
            state: data.state, 
            node: 'complete', 
            timestamp: data.timestamp || new Date().toISOString() 
          });
          setIsStreaming(false);
          isUserStoppedRef.current = false; // Reset for next stream
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
        // Only show error if connection is actually closed (readyState 2 = CLOSED) and not user-stopped
        if (eventSource.readyState === EventSource.CLOSED && isStreaming && !isUserStoppedRef.current) {
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

    // Show agent activity when node changes
    if (node && node !== lastNodeRef.current) {
      lastNodeRef.current = node;
      
      
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
              
              // Initialize edited draft with current draft when it's ready for approval
              if (state.is_halted || state.awaiting_human_approval) {
                setEditedDraft(state.current_draft);
              }
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
    if (state.is_halted || state.awaiting_human_approval) {
      if (state.current_draft) {
        // Has a draft, awaiting approval - initialize edited draft if not already set
        if (!editedDraft) {
          setEditedDraft(state.current_draft);
        }
        // Show approval section by default when first available (only once per approval state)
        // User can navigate back and forth with buttons after that
        if (!isApproved && !hasAutoShownEditorRef.current && !showApprovalSection) {
          setShowApprovalSection(true);
          hasAutoShownEditorRef.current = true;
        }
        // Don't show system message here - the editable draft editor will handle it
      } else {
        // Halted but no draft yet - might be an error
        addMessage({
          type: 'system',
          content: `Workflow paused. Waiting for next step...`,
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Show completion or approval status
    if (state.final_protocol || state.is_approved) {
      setIsApproved(true);
      setShowApprovalSection(false);
      // Only add message if we haven't already shown approval
      const hasApprovalMessage = messages.some(m => 
        m.type === 'system' && m.content.includes('approved')
      );
      if (!hasApprovalMessage) {
        addMessage({
          type: 'system',
          content: `✅ Protocol approved and finalized!`,
          timestamp: new Date().toISOString(),
        });
      }
    }
  };

  const handleApprove = async () => {
    if (!threadId || !currentState) return;

    try {
      // Use edited draft if user made changes, otherwise use original
      const draftToSend = editedDraft.trim() || currentState.current_draft || undefined;
      
      await api.approveProtocol(threadId, {
        edited_draft: draftToSend,
        feedback: undefined,
      });

      // Mark as approved and hide approval section
      setIsApproved(true);
      setShowApprovalSection(false);
      hasAutoShownEditorRef.current = false; // Reset for next time
      
      // Update current state to reflect approval
      setCurrentState({
        ...currentState,
        is_approved: true,
        final_protocol: draftToSend || currentState.current_draft,
        is_halted: false,
        awaiting_human_approval: false,
      });

      addMessage({
        type: 'system',
        content: `✅ Protocol approved and finalized!`,
        timestamp: new Date().toISOString(),
      });

      // Clear edited draft
      setEditedDraft('');
      setIsStreaming(false);
    } catch (err: any) {
      addMessage({
        type: 'system',
        content: `Error: ${err.message}`,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const handleBackToChat = () => {
    setShowApprovalSection(false);
    // Scroll to bottom of chat
    setTimeout(() => {
      scrollToBottom();
    }, 100);
  };

  const handleBackToEditor = () => {
    setShowApprovalSection(true);
    // Scroll to editor
    setTimeout(() => {
      const editorElement = document.querySelector('.approval-section');
      if (editorElement) {
        editorElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  const handleStop = () => {
    // Mark as user-stopped to prevent error messages
    isUserStoppedRef.current = true;
    
    // Close the EventSource connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    // Update state
    setIsStreaming(false);
    
    // Add a message indicating the workflow was stopped
      addMessage({
        type: 'system',
        content: `Workflow stopped by user.`,
        timestamp: new Date().toISOString(),
      });
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
          <div className="chat-header-left">
            <h1>Cerina Protocol Foundry</h1>
            <p>Autonomous CBT Exercise Design System</p>
          </div>
          {!showApprovalSection && currentState?.awaiting_human_approval && currentState?.current_draft && !isApproved && (
            <button onClick={handleBackToEditor} className="back-to-editor-button">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '6px' }}>
                <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Review & Edit Draft
            </button>
          )}
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

        {showApprovalSection && currentState?.awaiting_human_approval && currentState?.current_draft && !isApproved && (
          <div className="approval-section">
            <div className="approval-header">
              <div className="approval-header-content">
                <div>
                  <h3>Review & Edit Draft</h3>
                  <p className="approval-subtitle">You can edit the draft below. The preview shows how it will look. Changes will be saved when you click "Approve & Finalize".</p>
                </div>
                <button onClick={handleBackToChat} className="back-to-chat-button">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '6px' }}>
                    <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Back to Chat
                </button>
              </div>
            </div>
            <div className="draft-editor-wrapper">
              <div className="draft-editor-container">
                <div className="editor-tabs">
                  <button 
                    className={`tab-button ${!showSourceEditor ? 'active' : ''}`}
                    onClick={() => setShowSourceEditor(false)}
                  >
                    Preview (Document View)
                  </button>
                  <button 
                    className={`tab-button ${showSourceEditor ? 'active' : ''}`}
                    onClick={() => setShowSourceEditor(true)}
                  >
                    Edit Source (Real-time Preview)
                  </button>
                </div>
                <div className="editor-content">
                  {!showSourceEditor ? (
                    <div className="editor-preview-full">
                      <div className="preview-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {editedDraft || currentState.current_draft || ''}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ) : (
                    <div className="editor-split-view">
                      <div className="editor-textarea-container-split">
                        <div className="editor-label">Markdown Source</div>
                        <textarea
                          value={editedDraft || currentState.current_draft || ''}
                          onChange={(e) => setEditedDraft(e.target.value)}
                          className="draft-editor-split"
                          placeholder="Edit markdown source here... Preview updates in real-time on the right."
                          spellCheck={true}
                        />
                      </div>
                      <div className="editor-preview-split">
                        <div className="editor-label">Live Preview</div>
                        <div className="preview-content-split">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {editedDraft || currentState.current_draft || ''}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="approval-bar">
              <button onClick={handleApprove} className="approve-button">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '8px' }}>
                  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Approve & Finalize
              </button>
            </div>
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
          {isStreaming ? (
            <button
              type="button"
              onClick={handleStop}
              className="stop-button-icon"
              title="Stop generating"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="10" height="10" rx="1.5" fill="currentColor"/>
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="send-button"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

export default App;
