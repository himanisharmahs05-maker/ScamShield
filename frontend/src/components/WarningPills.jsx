import React from 'react';
import './SafeNavResults.css';

export const WarningPills = ({ flags = [] }) => {
  if (!flags || flags.length === 0) return null;
  return (
    <div className="warning-container">
      {flags.map((flag, idx) => (
        <span key={idx} className="warning-pill">⚠ {flag}</span>
      ))}
    </div>
  );
};