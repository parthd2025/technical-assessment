# Application Logs

This directory contains daily log files for the Clinical Note Processing API.

## Log Files

- **Format**: `clinical_api_YYYYMMDD.log`
- **Rotation**: Daily (automatic)
- **Retention**: Manage manually or implement rotation policy

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

## Example Log Entries

```
2026-03-04 10:15:23 - src.api - INFO - API Request: /api/v1/extract | note_length=450
2026-03-04 10:15:25 - src.llm_service - DEBUG - LLM Call: extract | model=llama-3.1-70b-versatile | tokens=456
2026-03-04 10:15:26 - src.api - INFO - API Response: /api/v1/extract | status=success | duration=1234.56ms
```

## Important Notes

- Logs may contain sensitive information - handle per HIPAA guidelines
- Review logs regularly for errors and performance issues
- Implement log rotation in production
- Consider using log aggregation tools (ELK, Splunk, etc.)
