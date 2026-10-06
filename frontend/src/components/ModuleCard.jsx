import React from 'react';
import { FieldRow } from './FieldRow';
import { WarningPills } from './WarningPills';
import './SafeNavResults.css';
export const ModuleCard = ({ title, icon, statusBadge, fields = [], warningFlags = [] }) => {
  return (
    <div className="module-card">
      <div className="card-header">
        <div className="card-title">
          <span style={{ fontSize: '14px' }}>{icon}</span> {title}
        </div>
        {statusBadge && (
          <div className={`status-badge ${statusBadge.color}`}>
            {statusBadge.text}
          </div>
        )}
      </div>
      <hr className="card-divider" />
      <div className="card-body">
        {fields.map((field, idx) => (
          <FieldRow 
            key={idx}
            label={field.label}
            value={field.value}
            type={field.type}
          />
        ))}
        <WarningPills flags={warningFlags} />
      </div>
    </div>
  );
};