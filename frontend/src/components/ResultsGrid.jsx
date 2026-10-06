import React from 'react';
import { ModuleCard } from './ModuleCard';
import './SafeNavResults.css';

export const ResultsGrid = ({ results }) => {
  if (!results || !results.details) return null;
  const d = results.details;
  const truncate = (str, len) => str?.length > len ? str.substring(0, len) + '…' : str;
  const link = d.link_structure || {};

  // --- SSL & Security Logic ---
  const ssl = d.ssl_security || {};
  let sslPills = [...(ssl.warning_flags || [])];
  if (ssl.is_self_signed) sslPills.push("Self-Signed Certificate");

  const sslBadge = ssl.is_valid 
    ? { text: "Connection Secured", color: 'badge-green' }
    : { text: "Unsecured", color: 'badge-red' };

  const isIdentityVerified = ssl.validation_type && ssl.validation_type.includes("OV/EV");
  const identityValue = isIdentityVerified 
    ? "Verified Business" 
    : "Hidden (Standard) ";

  const sslFields = [
    { 
      label: "Privacy (Encryption)", 
      value: ssl.is_valid ? 'Private 🔒' : 'Exposed 🔓' 
    },
    { 
      label: "Site Owner Identity", 
      value: identityValue 
    },
    { 
      label: "Security Provider", 
      value: truncate(ssl.issuer, 20) 
    },
    { 
      label: "Certificate Age", 
      value: ssl.days_to_expire ? `${ssl.days_to_expire} days remaining` : 'Unknown' 
    }
  ];

  // --- Phishing Checks Logic ---
  const phish = d.phishing_checks || {};
  const phishRisks = [phish.typosquatting, phish.brand_similarity, phish.suspicious_keywords, phish.homograph_attack]
    .some(v => v && v !== 'No' && v !== 'None' && v !== false);
    
  // ML augments the badge — High bucket → red, Medium → yellow, Unknown is ignored
  const mlBucket = phish.ml_risk_bucket || 'Unknown';
  const phishBadge = (phishRisks || mlBucket === 'High')  
    ? { text: "⚠ Risk Detected", color: 'badge-red' }  
    : mlBucket === 'Medium'  
    ? { text: "⚠ Possible Risk", color: 'badge-yellow' }  
    : { text: "Clean", color: 'badge-green' };

  const phishFields = [
    { label: "Typosquatting",        value: phish.typosquatting || 'No',          type: "phishing" },
    { label: "Brand Similarity",     value: phish.brand_similarity || 'None',      type: "phishing" },
    { label: "Suspicious Keywords",  value: phish.suspicious_keywords || 'No',     type: "phishing" },
    { label: "Homograph Attack",     value: phish.homograph_attack || 'No',        type: "phishing" },
    { label: "Obfuscation",          value: link.is_obfuscated ? 'Yes' : 'No',     type: "phishing" },
    { label: "ML Phishing Score",    value: phish.ml_phishing_probability ?? 'unknown', type: "ml-probability" },
    { label: "ML Risk Bucket",       value: mlBucket,                              type: "ml-bucket" }
  ];

  // --- IP Intelligence Logic ---
  const ip = d.ip_intelligence || {};
  
  const serverLocation = [ip.hosting_country, ip.hosting_flag, ip.hosting_city]
    .filter(Boolean)
    .join(' ');

  // Cleanly format the network provider/server name (e.g., "Google Cloud · AS15169")
  const networkProvider = [ip.asn_org || ip.isp, ip.asn]
    .filter(Boolean)
    .join(' · ');

  const ipBadge = { 
    text: `${ip.hosting_flag || ''} ${ip.hosting_city || ip.hosting_country || ''}`, 
    color: 'badge-neutral' 
  };
  
  const ipFields = [
    { label: "IP Address", value: ip.ip_address },
    { label: "Server Location", value: serverLocation || "Unknown" },
    { label: "Network Provider", value: networkProvider || "Unknown" },
    { label: "VPN / Proxy", value: ip.is_vpn_or_proxy, type: "boolean" },
    { label: "Is IP Based", value: link.is_ip_based, type: "boolean" } 
  ];

  return (
    <div className="results-grid">
      <ModuleCard title="SSL & Security" icon="🔐" statusBadge={sslBadge} fields={sslFields} warningFlags={sslPills} />
      <ModuleCard title="Phishing Checks" icon="🎣" statusBadge={phishBadge} fields={phishFields} />
      <ModuleCard title="IP Intelligence" icon="🌍" statusBadge={ipBadge} fields={ipFields} warningFlags={ip.warning_flags} />
    </div>
  );
};