import re
from typing import Dict, Any
import datetime

class VulnerabilityScanner:
    def __init__(self):
        self.rules = [
            # Security Rules
            {
                "pattern": r"(?i)(api[_-]?key|secret[_-]?key|password|token)\s*=\s*['\"]([^'\"]+)['\"]",
                "category": "Security",
                "description": "Hardcoded credentials or API keys",
                "severity": "Critical"
            },
            {
                "pattern": r"http://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/\S*)?",
                "category": "Network",
                "description": "Unsecured HTTP protocol usage",
                "severity": "Medium"
            },
            # Code Execution
            {
                "pattern": r"eval\(|exec\(|subprocess\.call|os\.system",
                "category": "Code Execution",
                "description": "Dangerous code execution",
                "severity": "Critical"
            },
            # SQL Injection
            {
                "pattern": r"f['\"]SELECT.*\{|f['\"]INSERT.*\{|f['\"]UPDATE.*\{|f['\"]DELETE.*\{",
                "category": "SQL Injection",
                "description": "Potential SQL injection via f-strings",
                "severity": "Critical"
            },
            # File Operations
            {
                "pattern": r"open\([^)]*['\"]w['\"]|open\([^)]*['\"]a['\"]",
                "category": "File Operation",
                "description": "Unsafe file write operation",
                "severity": "Medium"
            },
            # Input Validation
            {
                "pattern": r"input\(|raw_input\(",
                "category": "Input Validation",
                "description": "Unvalidated input usage",
                "severity": "Low"
            },
            # Exception Handling
            {
                "pattern": r"except:|except\s+Exception:|except\s+\w+:",
                "category": "Error Handling",
                "description": "Broad exception handling",
                "severity": "Low"
            },
            # Debug Settings
            {
                "pattern": r"DEBUG\s*=\s*True|DEVELOPMENT_MODE\s*=\s*True",
                "category": "Configuration",
                "description": "Debug mode enabled",
                "severity": "Medium"
            }
        ]

    def scan_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Scan code for potential vulnerabilities
        
        Args:
            code (str): Source code to scan
            language (str): Programming language of the code
            
        Returns:
            Dict containing scan results with findings
        """
        findings = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for rule in self.rules:
                matches = re.finditer(rule["pattern"], line)
                for match in matches:
                    finding = {
                        "severity": rule["severity"],
                        "category": rule["category"],
                        "description": rule["description"],
                        "line": line_num,
                        "code": line.strip(),
                        "match": match.group(0)
                    }
                    findings.append(finding)
        
        # Count findings by severity
        severity_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
        
        for finding in findings:
            severity_counts[finding["severity"]] += 1
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_findings": len(findings),
            "language": language,
            "findings": findings,
            "stats": {
                "severity_counts": severity_counts,
                "total_lines_scanned": len(lines)
            }
        }

def scan_code(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Convenience function to scan code without instantiating the scanner
    """
    scanner = VulnerabilityScanner()
    return scanner.scan_code(code, language)

def get_context(code: str, position: int, context_length: int) -> str:
    """Get surrounding context for a match"""
    start = max(0, position - context_length // 2)
    end = min(len(code), position + context_length // 2)
    return code[start:end].strip()

def get_severity_color(severity: str) -> str:
    """Get ANSI color code for severity level"""
    return {
        "Critical": "\033[91m",  # Red
        "High": "\033[93m",      # Yellow
        "Medium": "\033[94m",    # Blue
        "Low": "\033[92m"        # Green
    }.get(severity, "\033[0m")

def print_findings(scan_result: Dict[str, Any]) -> None:
    """
    Pretty print scan findings
    
    Args:
        scan_result (Dict): Result from scan_code()
    """
    print("\n=== Vulnerability Scan Results ===")
    print(f"Timestamp: {scan_result['timestamp']}")
    print(f"Total Findings: {scan_result['total_findings']}\n")
    
    stats = scan_result['stats']
    print("Summary:")
    print("Findings by Severity:")
    for severity, count in stats['severity_counts'].items():
        if count > 0:
            print(f"- {severity}: {count}")
    
    if scan_result['findings']:
        print("\nDetailed Findings:")
        for finding in scan_result['findings']:
            color = get_severity_color(finding['severity'])
            print(f"{color}[{finding['severity']}]\033[0m {finding['category']}")
            print(f"  ↳ {finding['description']}")
            print(f"  ↳ Line {finding['line']}: {finding['code']}")
    else:
        print("✅ No vulnerabilities found!")
