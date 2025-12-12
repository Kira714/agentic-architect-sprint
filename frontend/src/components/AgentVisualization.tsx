import { FoundryState } from '../types';
import './AgentVisualization.css';

interface AgentVisualizationProps {
  state: FoundryState;
}

const AGENT_COLORS: Record<string, string> = {
  supervisor: '#667eea',
  draftsman: '#48bb78',
  safety_guardian: '#f56565',
  clinical_critic: '#ed8936',
};

const AGENT_NAMES: Record<string, string> = {
  supervisor: 'Supervisor',
  draftsman: 'Draftsman',
  safety_guardian: 'Safety Guardian',
  clinical_critic: 'Clinical Critic',
};

export default function AgentVisualization({ state }: AgentVisualizationProps) {
  const currentAgent = state.current_agent;
  const notes = state.agent_notes || [];
  const recentNotes = notes.slice(-10).reverse();

  return (
    <div className="agent-visualization">
      <h3>Agent Activity</h3>
      
      <div className="agent-grid">
        {Object.entries(AGENT_NAMES).map(([key, name]) => {
          const isActive = currentAgent === key;
          const agentNotes = notes.filter(n => n.agent === key);
          
          return (
            <div
              key={key}
              className={`agent-card ${isActive ? 'active' : ''}`}
              style={{
                borderColor: isActive ? AGENT_COLORS[key] : '#e0e0e0',
                backgroundColor: isActive ? `${AGENT_COLORS[key]}10` : 'white',
              }}
            >
              <div className="agent-header">
                <div
                  className="agent-indicator"
                  style={{ backgroundColor: AGENT_COLORS[key] }}
                />
                <span className="agent-name">{name}</span>
                {isActive && <span className="active-badge">Active</span>}
              </div>
              <div className="agent-stats">
                <span>{agentNotes.length} notes</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="agent-notes">
        <h4>Recent Activity</h4>
        <div className="notes-list">
          {recentNotes.length === 0 ? (
            <div className="no-notes">No activity yet</div>
          ) : (
            recentNotes.map((note, idx) => (
              <div key={idx} className="note-item">
                <div className="note-header">
                  <span
                    className="note-agent"
                    style={{ color: AGENT_COLORS[note.agent] || '#666' }}
                  >
                    {AGENT_NAMES[note.agent] || note.agent}
                  </span>
                  <span className="note-time">
                    {new Date(note.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="note-message">{note.message}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {state.safety_review && (
        <div className="review-panel safety-review">
          <h4>🛡️ Safety Review</h4>
          <div className="review-status">
            Status: <strong>{state.safety_review.status}</strong>
          </div>
          {state.safety_review.concerns.length > 0 && (
            <div className="review-concerns">
              <strong>Concerns:</strong>
              <ul>
                {state.safety_review.concerns.map((concern, idx) => (
                  <li key={idx}>{concern}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {state.clinical_review && (
        <div className="review-panel clinical-review">
          <h4>🏥 Clinical Review</h4>
          <div className="review-status">
            Status: <strong>{state.clinical_review.status}</strong>
          </div>
          <div className="review-scores">
            <div>Empathy: {state.clinical_review.empathy_score.toFixed(1)}/10</div>
            <div>Tone: {state.clinical_review.tone_score.toFixed(1)}/10</div>
            <div>Structure: {state.clinical_review.structure_score.toFixed(1)}/10</div>
          </div>
          {state.clinical_review.feedback.length > 0 && (
            <div className="review-feedback">
              <strong>Feedback:</strong>
              <ul>
                {state.clinical_review.feedback.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}





