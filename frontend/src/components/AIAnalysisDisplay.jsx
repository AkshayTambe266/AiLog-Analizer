import React, { useState } from 'react';
import './AIAnalysisCard.css';

const AIAnalysisDisplay = ({ analysis, summary, modelUsed }) => {
    const [expandedIndex, setExpandedIndex] = useState(null);

    if (!analysis || analysis.length === 0) {
        return (
            <div className="ai-analysis-container">
                <div className="analysis-empty">
                    <p>🤔 No AI analysis available yet</p>
                    <small>Load logs to generate AI-powered error analysis</small>
                </div>
            </div>
        );
    }

    return (
        <div className="ai-analysis-container">
            {/* Summary Section */}
            {summary && (
                <div className="analysis-summary">
                    <h3>📊 Analysis Summary</h3>
                    <div className="summary-stats">
                        <div className="stat">
                            <span className="label">Total Errors:</span>
                            <span className="value">{summary.total_errors}</span>
                        </div>
                        {summary.critical_count > 0 && (
                            <div className="stat critical">
                                <span className="label">🚨 Critical:</span>
                                <span className="value">{summary.critical_count}</span>
                            </div>
                        )}
                        {summary.high_count > 0 && (
                            <div className="stat high">
                                <span className="label">⚠️ High:</span>
                                <span className="value">{summary.high_count}</span>
                            </div>
                        )}
                        {summary.medium_count > 0 && (
                            <div className="stat medium">
                                <span className="label">⏱️ Medium:</span>
                                <span className="value">{summary.medium_count}</span>
                            </div>
                        )}
                    </div>
                    <div className="recommendation">
                        <p>{summary.recommendation}</p>
                    </div>
                    {summary.top_affected_services && summary.top_affected_services.length > 0 && (
                        <div className="top-services">
                            <strong>Top Affected Services:</strong>
                            <ul>
                                {summary.top_affected_services.map((svc, idx) => (
                                    <li key={idx}>{svc.service} ({svc.count} errors)</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Individual Analysis Cards */}
            <div className="analysis-cards">
                <h3>🔍 Detailed Error Analysis ({analysis.length} analyzed)</h3>
                {analysis.map((item, idx) => (
                    <div
                        key={idx}
                        className={`analysis-card analysis-${item.severity?.toLowerCase() || 'medium'}`}
                        onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
                        style={{ cursor: 'pointer' }}
                    >
                        {/* Header */}
                        <div className="analysis-header">
                            <div className="severity-badge">
                                {item.severity === 'CRITICAL' && '🚨'}
                                {item.severity === 'HIGH' && '⚠️'}
                                {item.severity === 'MEDIUM' && '⏱️'}
                                {item.severity === 'LOW' && 'ℹ️'}
                                <span>{item.severity}</span>
                            </div>
                            <div className="error-message">
                                <strong>{item.error_message}</strong>
                                <small> - {item.service}</small>
                            </div>
                            <span className="expand-icon">
                                {expandedIndex === idx ? '▼' : '▶'}
                            </span>
                        </div>

                        {/* Expanded Content */}
                        {expandedIndex === idx && (
                            <div className="analysis-details">
                                <div className="detail-section">
                                    <strong>🎯 Root Cause:</strong>
                                    <p>{item.root_cause}</p>
                                </div>

                                <div className="detail-section">
                                    <strong>🛠️ Recommended Action:</strong>
                                    <p className="action-list">
                                        {item.recommended_action}
                                    </p>
                                </div>

                                <div className="detail-section">
                                    <strong>🛡️ Prevention Tips:</strong>
                                    <p>{item.prevention}</p>
                                </div>

                                {item.affected_component && (
                                    <div className="detail-section">
                                        <strong>📦 Affected Component:</strong>
                                        <p>{item.affected_component}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="analysis-footer">
                <small>
                    🤖 Analyzed with: <strong>{modelUsed === 'rule_based_fallback' ? 'Rule-Based Analyzer (Ollama unavailable)' : `Ollama (${modelUsed})`}</strong>
                </small>
            </div>
        </div>
    );
};

export default AIAnalysisDisplay;

