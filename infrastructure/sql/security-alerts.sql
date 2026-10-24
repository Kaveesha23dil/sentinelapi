-- Actual stored rule alerts; read-only. Use UTC and retain real evidence counts.
BEGIN READ ONLY;
SET LOCAL TIME ZONE 'UTC';
SELECT
    a.title,
    a.severity,
    a.risk_score,
    a.status,
    a.first_detected_at AS detected_at_utc,
    count(e.id) AS evidence_count
FROM security_alerts AS a
JOIN alert_evidence AS e ON e.alert_id = a.id
JOIN traffic_events AS t ON t.event_id = e.event_id
WHERE a.rule_id IS NOT NULL AND t.source = 'wso2-gateway'
GROUP BY a.id
ORDER BY a.first_detected_at DESC
LIMIT 10;
COMMIT;
