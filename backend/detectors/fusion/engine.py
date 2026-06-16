"""
Correlation / Fusion Engine
Groups findings from different detectors by temporal proximity
to create high-confidence incidents.

Rules:
  1 signal  = Low confidence
  2 signals = Medium confidence
  3+ signals = High confidence
"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class Incident:
    id: int
    start_time: float
    end_time: float
    findings: List[dict] = field(default_factory=list)
    severity: str = "low"
    confidence: float = 0.0
    detectors_involved: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "severity": self.severity,
            "confidence": self.confidence,
            "detectors_involved": self.detectors_involved,
            "finding_count": len(self.findings),
            "findings": self.findings,
        }


class FusionEngine:
    """
    Correlates findings from multiple detectors based on temporal overlap.
    Produces unified incidents with severity ratings.
    """

    def __init__(self, time_tolerance: float = 1.0):
        """
        Args:
            time_tolerance: Maximum time gap (seconds) to consider findings related
        """
        self.time_tolerance = time_tolerance

    def correlate(self, findings: List[dict]) -> List[dict]:
        """
        Group findings into correlated incidents.
        
        Args:
            findings: List of finding dicts with start_time, end_time, detector_type, etc.
            
        Returns:
            List of incident dicts
        """
        if not findings:
            return []

        # Separate temporal findings (have timestamps) from global findings
        temporal = [f for f in findings if f.get("start_time") is not None]
        global_findings = [f for f in findings if f.get("start_time") is None]

        # Sort temporal findings by start time
        temporal.sort(key=lambda f: f["start_time"])

        # Cluster findings by temporal proximity
        incidents = self._cluster_findings(temporal)

        # Add global findings (e.g., synthetic voice detection spanning entire file)
        # to all incidents or as their own incident
        if global_findings:
            if incidents:
                # Attach global findings to the highest-confidence incident
                best = max(incidents, key=lambda i: i.confidence)
                for gf in global_findings:
                    best.findings.append(gf)
                    if gf.get("detector_type") not in best.detectors_involved:
                        best.detectors_involved.append(gf["detector_type"])
                self._recalculate_severity(best)
            else:
                # Create a standalone incident from global findings
                incident = Incident(
                    id=1,
                    start_time=0.0,
                    end_time=global_findings[0].get("end_time", 0.0),
                    findings=global_findings,
                )
                for gf in global_findings:
                    if gf.get("detector_type") not in incident.detectors_involved:
                        incident.detectors_involved.append(gf["detector_type"])
                self._recalculate_severity(incident)
                incidents.append(incident)

        # Sort by start time and assign IDs
        incidents.sort(key=lambda i: i.start_time)
        for i, inc in enumerate(incidents, 1):
            inc.id = i

        return [inc.to_dict() for inc in incidents]

    def _cluster_findings(self, temporal_findings: List[dict]) -> List["Incident"]:
        """Cluster findings by time proximity."""
        if not temporal_findings:
            return []

        incidents: List[Incident] = []
        current_incident = Incident(
            id=0,
            start_time=temporal_findings[0]["start_time"],
            end_time=temporal_findings[0].get("end_time", temporal_findings[0]["start_time"]),
            findings=[temporal_findings[0]],
            detectors_involved=[temporal_findings[0].get("detector_type", "unknown")],
        )

        for finding in temporal_findings[1:]:
            f_start = finding["start_time"]

            # Check if this finding is close enough to the current incident
            if f_start <= current_incident.end_time + self.time_tolerance:
                # Merge into current incident
                current_incident.findings.append(finding)
                current_incident.end_time = max(
                    current_incident.end_time,
                    finding.get("end_time", f_start)
                )
                det = finding.get("detector_type", "unknown")
                if det not in current_incident.detectors_involved:
                    current_incident.detectors_involved.append(det)
            else:
                # Finalize current incident and start new one
                self._recalculate_severity(current_incident)
                incidents.append(current_incident)

                current_incident = Incident(
                    id=0,
                    start_time=f_start,
                    end_time=finding.get("end_time", f_start),
                    findings=[finding],
                    detectors_involved=[finding.get("detector_type", "unknown")],
                )

        # Don't forget the last incident
        self._recalculate_severity(current_incident)
        incidents.append(current_incident)

        return incidents

    def _recalculate_severity(self, incident: Incident):
        """Calculate severity based on number of corroborating signals."""
        n_detectors = len(set(incident.detectors_involved))
        n_findings = len(incident.findings)

        # Severity rules
        if n_detectors >= 3:
            incident.severity = "high"
        elif n_detectors >= 2:
            incident.severity = "medium"
        else:
            incident.severity = "low"

        # Confidence: weighted average boosted by corroboration
        confidences = [f.get("confidence", 0.5) for f in incident.findings]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.5

        # Boost for multi-detector corroboration
        boost = 1.0 + (n_detectors - 1) * 0.15
        incident.confidence = round(min(avg_conf * boost, 0.99), 3)
