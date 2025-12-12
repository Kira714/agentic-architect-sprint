import { useState, useEffect } from 'react';
import type { ChatMessage as ChatMessageType } from '../App';
import { UserIcon, AssistantIcon, ThinkingIcon, DocumentIcon } from './Icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ChatMessage.css';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export default function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const [displayedContent, setDisplayedContent] = useState(message.content);

  useEffect(() => {
    // Always sync with message content (backend streams character by character)
    setDisplayedContent(message.content);
  }, [message.content]);

  const getMessageClass = () => {
    switch (message.type) {
      case 'user':
        return 'user-message';
      case 'agent':
      case 'response':
        return 'assistant-message';
      case 'thinking':
        return 'thinking-message';
      case 'draft':
        return 'draft-message';
      default:
        return 'message';
    }
  };

  const renderContent = () => {
    const content = displayedContent;
    const shouldShowCursor = isStreaming && (message.type === 'thinking' || message.type === 'response' || message.type === 'agent');

    // Use markdown for assistant messages, plain text for user
    if (message.type === 'user') {
      return <div className="message-text">{content}</div>;
    }

    // For drafts, use markdown
    if (message.type === 'draft') {
      return (
        <div className="draft-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          {shouldShowCursor && <span className="typing-cursor">▊</span>}
        </div>
      );
    }

    // For thinking, show with subtle styling (no markdown, plain text)
    if (message.type === 'thinking') {
      return (
        <div className="thinking-content">
          {content}
          {shouldShowCursor && <span className="typing-cursor">▊</span>}
        </div>
      );
    }

    // For assistant messages, use markdown
    return (
      <div className="message-text">
        <ReactMarkdown>{content}</ReactMarkdown>
        {shouldShowCursor && <span className="typing-cursor">▊</span>}
      </div>
    );
  };

  return (
    <div className={`message ${getMessageClass()}`}>
      <div className="message-avatar">
        {message.type === 'user' ? (
          <div className="avatar-circle user-avatar">
            <UserIcon />
          </div>
        ) : message.type === 'thinking' ? (
          <div className="avatar-circle thinking-avatar">
            <ThinkingIcon />
          </div>
        ) : message.type === 'draft' ? (
          <div className="avatar-circle draft-avatar">
            <DocumentIcon />
          </div>
        ) : (
          <div className="avatar-circle assistant-avatar">
            <AssistantIcon />
          </div>
        )}
      </div>

      <div className="message-content-wrapper">
        <div className="message-content">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
