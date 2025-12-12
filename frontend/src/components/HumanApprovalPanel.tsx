import { useState } from 'react';
import './HumanApprovalPanel.css';

interface HumanApprovalPanelProps {
  draft: string;
  onApprove: (editedDraft?: string, feedback?: string) => void;
}

export default function HumanApprovalPanel({ draft, onApprove }: HumanApprovalPanelProps) {
  const [editedDraft, setEditedDraft] = useState(draft);
  const [feedback, setFeedback] = useState('');
  const [isApproving, setIsApproving] = useState(false);

  const handleApprove = async () => {
    setIsApproving(true);
    const finalDraft = editedDraft !== draft ? editedDraft : undefined;
    await onApprove(finalDraft, feedback || undefined);
    setIsApproving(false);
  };

  return (
    <div className="human-approval-panel">
      <div className="approval-header">
        <h3>⏸️ Human-in-the-Loop Review</h3>
        <p>The system has paused for your review. Please review the draft, make any edits, and approve to continue.</p>
      </div>

      <div className="approval-content">
        <div className="draft-editor">
          <label>Edit Draft (if needed):</label>
          <textarea
            value={editedDraft}
            onChange={(e) => setEditedDraft(e.target.value)}
            rows={20}
            className="draft-textarea"
          />
        </div>

        <div className="feedback-section">
          <label>Feedback (optional):</label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Add any feedback or notes..."
            rows={4}
            className="feedback-textarea"
          />
        </div>

        <div className="approval-actions">
          <button
            onClick={handleApprove}
            disabled={isApproving}
            className="approve-button"
          >
            {isApproving ? 'Approving...' : '✅ Approve & Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}





