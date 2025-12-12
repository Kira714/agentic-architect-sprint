import { FoundryState } from '../types';
import './DraftViewer.css';

interface DraftViewerProps {
  state: FoundryState;
}

export default function DraftViewer({ state }: DraftViewerProps) {
  const draft = state.current_draft || state.final_protocol;
  const version = state.current_version;
  const versions = state.draft_versions || [];

  if (!draft) {
    return (
      <div className="draft-viewer">
        <h3>Draft</h3>
        <div className="no-draft">No draft yet. Agents are working...</div>
      </div>
    );
  }

  return (
    <div className="draft-viewer">
      <div className="draft-header">
        <h3>CBT Exercise Protocol</h3>
        <div className="draft-meta">
          <span>Version {version}</span>
          <span>•</span>
          <span>{versions.length} iterations</span>
        </div>
      </div>
      
      <div className="draft-content">
        <pre>{draft}</pre>
      </div>

      {versions.length > 1 && (
        <div className="version-history">
          <h4>Version History</h4>
          <div className="versions-list">
            {versions.map((v) => (
              <div key={v.version} className="version-item">
                <div className="version-header">
                  <span>v{v.version}</span>
                  <span className="version-time">
                    {new Date(v.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="version-agent">
                  Created by: {v.created_by}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}





