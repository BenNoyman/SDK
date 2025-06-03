import re
from typing import Dict, Any, List
import datetime
import tempfile
import subprocess
import json
import os

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

class SemgrepScanner:
    """
    Wraps the Semgrep CLI to return findings in the same dict format
    as VulnerabilityScanner.
    """
    def __init__(self, config_path: str = "p/ci"):
        self.config = config_path

    def scan_code(self, code: str) -> List[Dict[str, Any]]:
        # write the code to a tmp file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(code)
            tmp.flush()
            tmp_path = tmp.name

        try:
            # invoke semgrep CLI (returncode 1 = findings found)
            proc = subprocess.run(
                ["semgrep", "--config", self.config, "--json", tmp_path],
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            if proc.returncode > 1:
                raise RuntimeError(f"Semgrep error: {proc.stderr.strip()}")

            data = json.loads(proc.stdout)
            results: List[Dict[str, Any]] = []
            for r in data.get("results", []):
                # Map Semgrep severity to our format
                semgrep_severity = r.get("extra", {}).get("metadata", {}).get("severity", "Medium")
                # Normalize severity levels
                if semgrep_severity.lower() in ["error", "warning", "info"]:
                    severity_map = {"error": "Critical", "warning": "Medium", "info": "Low"}
                    severity = severity_map.get(semgrep_severity.lower(), "Medium")
                else:
                    severity = semgrep_severity

                results.append({
                    "severity":    severity,
                    "category":    r.get("check_id", "semgrep"),
                    "description": r.get("extra", {}).get("message", r.get("message", "")),
                    "line":        r["start"]["line"],
                    "code":        r.get("extra", {}).get("lines", "").strip(),
                    "match":       r.get("extra", {}).get("match", "")
                })
            return results
        except FileNotFoundError:
            print("⚠️ Semgrep not found. Install with: pip install semgrep")
            return []
        except json.JSONDecodeError:
            print("⚠️ Failed to parse Semgrep output")
            return []
        except UnicodeDecodeError:
            print("⚠️ Semgrep encoding error, falling back to regex scanner only")
            return []
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

def scan_code(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Run both the regex-based VulnerabilityScanner and SemgrepScanner,
    merge & dedupe their findings, then recompute severity stats.
    """
    # Initialize both scanners
    regex = VulnerabilityScanner()
    semgrep = SemgrepScanner(config_path=os.getenv("SEMGREP_CONFIG", "p/ci"))

    # 1) Run regex engine
    base = regex.scan_code(code, language)
    findings = base["findings"]

    # 2) Run semgrep engine (gracefully handle errors)
    try:
        semgrep_findings = semgrep.scan_code(code)
        findings.extend(semgrep_findings)
        print(f"✅ Regex scanner found {len(base['findings'])} findings, Semgrep found {len(semgrep_findings)} findings")
    except Exception as e:
        print(f"⚠️ Semgrep scan failed: {e}")

    # 3) Dedupe by (line, match, description)
    unique = {(f["line"], f["match"], f["description"]): f for f in findings}
    merged = list(unique.values())

    # 4) Recompute severity counts
    severity_counts = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0
    }
    
    for f in merged:
        severity_counts.setdefault(f["severity"], 0)
        severity_counts[f["severity"]] += 1

    return {
        "timestamp":          datetime.datetime.utcnow().isoformat(),
        "total_findings":     len(merged),
        "language":           language,
        "findings":           merged,
        "stats": {
            "severity_counts":    severity_counts,
            "total_lines_scanned": len(code.splitlines())
        }
    }

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
