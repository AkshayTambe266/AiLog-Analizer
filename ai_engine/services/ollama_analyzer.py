"""
🦙 Ollama AI Analyzer Service
Specialized service for analyzing ERROR logs using Ollama LLM
Production-grade implementation with error handling and fallbacks
"""

import json
import logging
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OllamaAnalyzer:
    """Specialized service for analyzing ERROR logs using Ollama"""

    def __init__(self):
        """Initialize Ollama analyzer with configuration"""
        self.ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", "mistral")
        self.timeout = 120  # 2 minutes timeout for analysis
        self.connected = self._check_connection()

    def _check_connection(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m.get("name", "") for m in models]
                
                if self.model_name in available_models or any(self.model_name in m for m in available_models):
                    print(f"✅ [OLLAMA] Connected - Model: {self.model_name}")
                    return True
                else:
                    print(f"⚠️ [OLLAMA] Available models: {available_models}")
                    # Try to use first available model
                    if available_models:
                        self.model_name = available_models[0]
                        print(f"⚠️ [OLLAMA] Using available model: {self.model_name}")
                        return True
        except Exception as e:
            print(f"❌ [OLLAMA] Connection failed: {str(e)}")
            print(f"   Make sure Ollama is running: ollama serve")
            print(f"   URL: {self.ollama_url}")

        return False

    def analyze_error_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze ERROR logs using Ollama AI

        Args:
            logs: List of ERROR log documents

        Returns:
            Analysis results with root causes and recommendations
        """
        if not logs:
            return {
                "status": "success",
                "total_analyzed": 0,
                "analyses": [],
                "summary": "No error logs to analyze",
                "timestamp": datetime.now().isoformat()
            }

        try:
            if not self.connected:
                print("[WARN] Ollama not available - using rule-based analysis")
                return self._rule_based_analysis(logs)

            analyses = []
            
            # Analyze each error log
            for i, log in enumerate(logs[:20]):  # Analyze first 20 errors
                error_analysis = self._analyze_single_error(log, i)
                if error_analysis:
                    analyses.append(error_analysis)

            # Generate summary insights
            summary = self._generate_summary(logs, analyses)

            return {
                "status": "success",
                "total_analyzed": len(logs),
                "analyses": analyses,
                "summary": summary,
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Ollama analysis error: {str(e)}")
            print(f"[ERROR] Ollama analysis failed: {str(e)}")
            return self._rule_based_analysis(logs)

    def _analyze_single_error(self, log: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Analyze a single error log using Ollama"""
        try:
            message = log.get("message", "Unknown error")
            service = log.get("service", "unknown")
            timestamp = log.get("@timestamp", log.get("timestamp", ""))

            # Build analysis prompt
            prompt = f"""Analyze this application ERROR log and provide insights:

ERROR MESSAGE: {message}
SERVICE: {service}
TIMESTAMP: {timestamp}

Provide a JSON response with:
1. root_cause: (string) What likely caused this error?
2. severity: (string) CRITICAL/HIGH/MEDIUM/LOW
3. affected_component: (string) What part of the system is affected?
4. recommended_action: (string) What should be done to fix this?
5. prevention: (string) How can this be prevented in future?

Respond ONLY with valid JSON, no additional text."""

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                    "top_k": 10,
                    "top_p": 0.9
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result_text = response.json().get("response", "")
                
                # Parse JSON from response
                analysis = self._parse_ollama_response(result_text)
                
                if analysis:
                    analysis["error_message"] = message
                    analysis["service"] = service
                    analysis["log_index"] = index
                    return analysis

        except Exception as e:
            logger.warning(f"Failed to analyze error {index}: {str(e)}")

        return None

    def _parse_ollama_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Ollama response"""
        try:
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse Ollama response: {str(e)}")

        return None

    def _rule_based_analysis(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback rule-based analysis when Ollama is unavailable"""
        analyses = []
        
        for i, log in enumerate(logs[:20]):
            message = log.get("message", "Unknown error")
            service = log.get("service", "unknown")
            
            analysis = {
                "error_message": message,
                "service": service,
                "log_index": i,
                "root_cause": self._extract_root_cause(message),
                "severity": self._extract_severity(message),
                "affected_component": service,
                "recommended_action": self._get_recommended_action(message),
                "prevention": self._get_prevention_tips(message),
                "analysis_type": "rule_based"
            }
            analyses.append(analysis)

        summary = self._generate_summary(logs, analyses)

        return {
            "status": "success",
            "total_analyzed": len(logs),
            "analyses": analyses,
            "summary": summary,
            "model_used": "rule_based_fallback",
            "timestamp": datetime.now().isoformat()
        }

    def _extract_root_cause(self, message: str) -> str:
        """Extract likely root cause from error message"""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ["timeout", "timed out", "exceeded"]):
            return "Request timeout - service or database response too slow"
        elif any(word in msg_lower for word in ["connection refused", "connection reset", "unreachable", "no route"]):
            return "Network connectivity issue - service unavailable or firewall blocking"
        elif any(word in msg_lower for word in ["permission denied", "unauthorized", "forbidden", "403", "401"]):
            return "Authentication or authorization failure"
        elif any(word in msg_lower for word in ["out of memory", "heap space", "memory exhausted"]):
            return "Memory exhaustion - application needs more RAM"
        elif any(word in msg_lower for word in ["null pointer", "nullpointerexception", "none type", "undefined"]):
            return "Null reference or missing object - code bug"
        elif any(word in msg_lower for word in ["file not found", "no such file", "cannot find", "not exists"]):
            return "Missing file or resource"
        elif any(word in msg_lower for word in ["database", "sql", "query"]):
            return "Database issue - query failure or connection problem"
        else:
            return "Application error - check logs for details"

    def _extract_severity(self, message: str) -> str:
        """Determine severity level from error message"""
        msg_lower = message.lower()
        
        critical_keywords = ["fatal", "crashed", "critical", "panic", "outage", "down"]
        high_keywords = ["error", "failed", "exception", "timeout", "refused"]
        medium_keywords = ["warning", "deprecated", "slow", "retry"]
        
        if any(k in msg_lower for k in critical_keywords):
            return "CRITICAL"
        elif any(k in msg_lower for k in high_keywords):
            return "HIGH"
        elif any(k in msg_lower for k in medium_keywords):
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommended_action(self, message: str) -> str:
        """Get recommended action to fix the error"""
        msg_lower = message.lower()
        
        if "timeout" in msg_lower:
            return "1. Check service response time\n2. Increase timeout value\n3. Optimize database queries\n4. Scale up resources"
        elif "connection" in msg_lower or "unreachable" in msg_lower:
            return "1. Verify service is running\n2. Check network connectivity\n3. Review firewall rules\n4. Check service configuration"
        elif "memory" in msg_lower or "heap" in msg_lower:
            return "1. Increase JVM heap size\n2. Check for memory leaks\n3. Optimize memory usage\n4. Restart service"
        elif "permission" in msg_lower or "denied" in msg_lower:
            return "1. Verify user credentials\n2. Check access control lists\n3. Review security policies\n4. Update permissions"
        elif "null" in msg_lower or "exception" in msg_lower:
            return "1. Review application logs\n2. Check code for null references\n3. Add input validation\n4. Fix the bug"
        else:
            return "1. Review detailed error logs\n2. Check system resources\n3. Monitor service health\n4. Contact support if needed"

    def _get_prevention_tips(self, message: str) -> str:
        """Get prevention tips for similar errors"""
        msg_lower = message.lower()
        
        if "timeout" in msg_lower:
            return "Add connection pooling, implement caching, optimize queries"
        elif "memory" in msg_lower:
            return "Monitor memory usage, implement garbage collection, use memory pools"
        elif "connection" in msg_lower:
            return "Use service discovery, implement health checks, add retry logic"
        else:
            return "Implement comprehensive error handling, add logging, setup monitoring"

    def _generate_summary(self, logs: List[Dict[str, Any]], analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary insights from all analyses"""
        if not analyses:
            return {
                "total_errors": len(logs),
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "top_services": [],
                "top_root_causes": [],
                "recommendation": "No errors to analyze"
            }

        # Count severity levels
        severity_counts = {
            "CRITICAL": sum(1 for a in analyses if a.get("severity") == "CRITICAL"),
            "HIGH": sum(1 for a in analyses if a.get("severity") == "HIGH"),
            "MEDIUM": sum(1 for a in analyses if a.get("severity") == "MEDIUM"),
            "LOW": sum(1 for a in analyses if a.get("severity") == "LOW")
        }

        # Count affected services
        services = {}
        for analysis in analyses:
            service = analysis.get("service", "unknown")
            services[service] = services.get(service, 0) + 1

        top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:3]

        # Count root causes
        root_causes = {}
        for analysis in analyses:
            cause = analysis.get("root_cause", "unknown")
            root_causes[cause] = root_causes.get(cause, 0) + 1

        top_causes = sorted(root_causes.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "total_errors": len(logs),
            "critical_count": severity_counts["CRITICAL"],
            "high_count": severity_counts["HIGH"],
            "medium_count": severity_counts["MEDIUM"],
            "low_count": severity_counts["LOW"],
            "top_affected_services": [{"service": s[0], "count": s[1]} for s in top_services],
            "top_root_causes": [{"cause": c[0], "count": c[1]} for c in top_causes],
            "recommendation": self._get_recommendation(severity_counts, top_services),
            "action_required": severity_counts["CRITICAL"] > 0 or severity_counts["HIGH"] > 2
        }

    def _get_recommendation(self, severity_counts: Dict[str, int], top_services: List) -> str:
        """Generate overall recommendation"""
        if severity_counts["CRITICAL"] > 0:
            service = top_services[0][0] if top_services else "application"
            return f"🚨 URGENT: {severity_counts['CRITICAL']} critical errors in {service} - Immediate action required!"
        elif severity_counts["HIGH"] > 2:
            return f"⚠️ HIGH: {severity_counts['HIGH']} high-severity errors detected - Investigation recommended"
        elif severity_counts["MEDIUM"] > 5:
            return f"⏱️ MEDIUM: {severity_counts['MEDIUM']} medium-severity errors - Plan maintenance"
        else:
            return "✅ OK: Error levels are within acceptable range - Continue monitoring"

