# Redis Debugging Commands for Solicitation Deconstruction

This document provides Redis CLI commands for manual verification and debugging of the solicitation deconstruction workflow.

## Prerequisites

1. Ensure Redis is running locally or accessible
2. Install Redis CLI: `brew install redis` (macOS) or `apt-get install redis-tools` (Ubuntu)
3. Connect to Redis: `redis-cli` (default: localhost:6379)

## Job Status Debugging

### Check Job Status
```bash
# Get job status
redis-cli GET "job:{job_id}:status"

# Example:
redis-cli GET "job:123e4567-e89b-12d3-a456-426614174000:status"
```

### Check Job Metadata
```bash
# Get complete job metadata
redis-cli GET "job:{job_id}:metadata"

# Get job result (if completed)
redis-cli GET "job:{job_id}:result"

# Get job error (if failed)
redis-cli GET "job:{job_id}:error"
```

### List All Jobs
```bash
# Find all job keys
redis-cli KEYS "job:*"

# Find all job status keys
redis-cli KEYS "job:*:status"

# Find all job result keys
redis-cli KEYS "job:*:result"
```

## Queue Debugging (RQ Integration)

### Check RQ Queues
```bash
# List all RQ queues
redis-cli KEYS "rq:queue:*"

# Check default queue length
redis-cli LLEN "rq:queue:default"

# Check failed queue
redis-cli LLEN "rq:queue:failed"
```

### Inspect Queue Jobs
```bash
# Get jobs in default queue
redis-cli LRANGE "rq:queue:default" 0 -1

# Get failed jobs
redis-cli LRANGE "rq:queue:failed" 0 -1
```

## Workflow Verification Commands

### Complete Job Lifecycle Check
```bash
#!/bin/bash
# Save as check_job.sh and run: ./check_job.sh {job_id}

JOB_ID=$1
echo "=== Job Status Check for $JOB_ID ==="

echo "Status:"
redis-cli GET "job:$JOB_ID:status"

echo "Progress:"
redis-cli GET "job:$JOB_ID:progress"

echo "Created At:"
redis-cli GET "job:$JOB_ID:created_at"

echo "Result (first 200 chars):"
redis-cli GET "job:$JOB_ID:result" | head -c 200

echo "Error (if any):"
redis-cli GET "job:$JOB_ID:error"
```

### Monitor Job Progress
```bash
#!/bin/bash
# Save as monitor_job.sh and run: ./monitor_job.sh {job_id}

JOB_ID=$1
echo "Monitoring job: $JOB_ID"

while true; do
    STATUS=$(redis-cli GET "job:$JOB_ID:status")
    PROGRESS=$(redis-cli GET "job:$JOB_ID:progress")
    
    echo "$(date): Status=$STATUS, Progress=$PROGRESS%"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo "Job finished with status: $STATUS"
        break
    fi
    
    sleep 5
done
```

## Data Validation Commands

### Validate StructuredSolicitation Result
```bash
# Get and pretty-print the result JSON
redis-cli GET "job:{job_id}:result" | jq '.'

# Check specific fields
redis-cli GET "job:{job_id}:result" | jq '.solicitation_id'
redis-cli GET "job:{job_id}:result" | jq '.award_title'
redis-cli GET "job:{job_id}:result" | jq '.required_scientific_skills'
redis-cli GET "job:{job_id}:result" | jq '.pi_eligibility_rules'
```

### Count Extracted Data
```bash
# Count required skills
redis-cli GET "job:{job_id}:result" | jq '.required_scientific_skills | length'

# Count PI eligibility rules
redis-cli GET "job:{job_id}:result" | jq '.pi_eligibility_rules | length'

# Count extracted sections
redis-cli GET "job:{job_id}:result" | jq '.extracted_sections | keys | length'

# Get full text length
redis-cli GET "job:{job_id}:result" | jq '.full_text | length'
```

## Cleanup Commands

### Clean Up Test Jobs
```bash
# Delete specific job data
redis-cli DEL "job:{job_id}:status"
redis-cli DEL "job:{job_id}:result"
redis-cli DEL "job:{job_id}:error"
redis-cli DEL "job:{job_id}:metadata"

# Or delete all job data for a specific job
redis-cli KEYS "job:{job_id}:*" | xargs redis-cli DEL
```

### Clean Up All Test Data
```bash
# WARNING: This deletes ALL job data
redis-cli KEYS "job:*" | xargs redis-cli DEL

# Clean up RQ queues (use with caution)
redis-cli DEL "rq:queue:default"
redis-cli DEL "rq:queue:failed"
```

## Troubleshooting Commands

### Check Redis Connection
```bash
# Test Redis connectivity
redis-cli ping
# Should return: PONG

# Check Redis info
redis-cli info server
```

### Monitor Redis Activity
```bash
# Monitor all Redis commands in real-time
redis-cli monitor

# Monitor specific key patterns
redis-cli --latency-history -i 1
```

### Check Memory Usage
```bash
# Check Redis memory usage
redis-cli info memory

# Check memory usage by key pattern
redis-cli --bigkeys
```

## Example Workflow

1. **Upload PDF via Postman** → Get job_id
2. **Check initial status**: `redis-cli GET "job:{job_id}:status"`
3. **Monitor progress**: Use monitor script or manual polling
4. **Validate result**: `redis-cli GET "job:{job_id}:result" | jq '.'`
5. **Clean up**: `redis-cli KEYS "job:{job_id}:*" | xargs redis-cli DEL`

## Integration with Postman

You can use these Redis commands alongside the Postman collection to:

1. Verify that jobs are being created in Redis when you upload PDFs
2. Monitor background processing progress
3. Validate that results are stored correctly
4. Debug any issues with job state management
5. Clean up test data between test runs

## Notes

- Replace `{job_id}` with actual job IDs from your Postman tests
- Ensure Redis is accessible from your testing environment
- Use `jq` for JSON formatting: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
- Be careful with cleanup commands in production environments