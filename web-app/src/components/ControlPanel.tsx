import React from 'react';

interface ControlPanelProps {
  viewMode: 'karaoke' | 'syllables' | 'simple';
  onViewModeChange: (mode: 'karaoke' | 'syllables' | 'simple') => void;
  showTranslations: boolean;
  onTranslationsToggle: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  viewMode,
  onViewModeChange,
  showTranslations,
  onTranslationsToggle,
}) => {
  return (
    <div className="control-panel">
      <div className="view-mode-controls">
        <label>View Mode:</label>
        <select 
          value={viewMode} 
          onChange={(e) => onViewModeChange(e.target.value as any)}
        >
          <option value="karaoke">Karaoke</option>
          <option value="syllables">Syllables</option>
          <option value="simple">Simple</option>
        </select>
      </div>
      
      <div className="translation-controls">
        <label>
          <input
            type="checkbox"
            checked={showTranslations}
            onChange={onTranslationsToggle}
          />
          Show Translations
        </label>
      </div>
    </div>
  );
};