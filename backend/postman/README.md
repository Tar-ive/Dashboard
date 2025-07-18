# Postman Collections for NSF Solicitation Deconstruction API

This directory contains Postman collections and documentation for testing the NSF Solicitation Deconstruction API.

## Files

- **`Solicitation_Deconstruction_Collection.json`** - Main Postman collection for testing the complete workflow
- **`Redis_Debugging_Commands.md`** - Redis CLI commands for manual verification and debugging
- **`README.md`** - This documentation file

## Quick Start

### 1. Import Collection

1. Open Postman
2. Click "Import" button
3. Select `Solicitation_Deconstruction_Collection.json`
4. The collection will be imported with all requests and tests

### 2. Set Environment Variables

Create a new environment in Postman with these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `job_id` | (auto-set) | Current job ID for testing |
| `max_poll_attempts` | `20` | Maximum polling attempts |
| `poll_interval_ms` | `5000` | Polling interval in milliseconds |

### 3. Prepare Test File

Ensure you have a sample PDF file available:
- Use one of the existing files in `backend/data/uploads/`
- Recommended: `NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf`

### 4. Run Complete Workflow

Execute requests in order:

1. **Upload PDF Solicitation** - Uploads PDF and gets job_id
2. **Check Job Status (Single)** - Manual status check
3. **Poll Job Status (Automated)** - Automated polling until completion
4. **Validate Structured Result** - Comprehensive result validation
5. **Cleanup Job (Optional)** - Clean up test data

## Collection Features

### Automated Job ID Management
- Upload request automatically saves job_id to environment
- Subsequent requests use the saved job_id
- No manual copying required

### Intelligent Polling
- Automated polling with configurable intervals
- Stops when job completes or fails
- Respects maximum attempt limits
- Detailed console logging

### Comprehensive Validation
- Validates API response structure
- Checks StructuredSolicitation model compliance
- Verifies data types and required fields
- Logs detailed result information

### Error Handling
- Handles failed jobs gracefully
- Provides detailed error information
- Validates error response structure

## Test Scenarios

### Happy Path
1. Upload valid PDF → Get job_id
2. Poll status → Job progresses through queued → processing → completed
3. Validate result → StructuredSolicitation with all required fields
4. Cleanup → Job data removed

### Error Scenarios
- Invalid file type (non-PDF)
- File too large (>10MB)
- Empty file
- Non-existent job_id
- Job processing failures

## Redis Debugging

Use the commands in `Redis_Debugging_Commands.md` to:

- Monitor job status in Redis
- Inspect job results and errors
- Debug RQ queue operations
- Validate data storage
- Clean up test data

### Example Redis Workflow

```bash
# 1. Check job was created
redis-cli GET "job:{job_id}:status"

# 2. Monitor progress
redis-cli GET "job:{job_id}:progress"

# 3. Validate result
redis-cli GET "job:{job_id}:result" | jq '.'

# 4. Clean up
redis-cli KEYS "job:{job_id}:*" | xargs redis-cli DEL
```

## Expected Results

### Successful Upload Response
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "PDF uploaded successfully. Processing started."
}
```

### Job Status Response (Processing)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": 45,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z"
}
```

### Completed Job with StructuredSolicitation
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100,
  "result": {
    "solicitation_id": "NSF-24-569",
    "award_title": "Mathematical Foundations of Artificial Intelligence",
    "funding_ceiling": 1500000,
    "project_duration_months": 60,
    "pi_eligibility_rules": [
      "Must be affiliated with eligible institution",
      "Must have relevant research experience"
    ],
    "required_scientific_skills": [
      "Machine Learning",
      "Mathematical Modeling",
      "Algorithm Development"
    ],
    "full_text": "...",
    "extracted_sections": {
      "Eligibility": "...",
      "Award Information": "..."
    },
    "processing_time_seconds": 45.2,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:45Z",
  "processing_time_seconds": 45.2
}
```

## Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file is valid PDF
   - Verify file size < 10MB
   - Ensure correct form-data key: "file"

2. **Job Not Found**
   - Verify job_id is set in environment
   - Check Redis connection
   - Confirm job was created successfully

3. **Polling Timeout**
   - Increase `max_poll_attempts`
   - Check background worker is running
   - Monitor Redis for job progress

4. **Invalid Results**
   - Check LLM integration is working
   - Verify PDF text extraction
   - Review error messages in Redis

### Debug Steps

1. Check API server is running: `curl http://localhost:8000/docs`
2. Verify Redis connection: `redis-cli ping`
3. Monitor Redis activity: `redis-cli monitor`
4. Check server logs for errors
5. Use Redis debugging commands for detailed inspection

## Performance Notes

- PDF processing typically takes 30-120 seconds
- Polling interval of 5 seconds is recommended
- Large PDFs (>5MB) may take longer to process
- LLM API calls add 10-30 seconds per section

## Next Steps

After validating Milestone 1 (Solicitation Deconstruction):

1. Proceed to Milestone 2 (Dream Team Assembly)
2. Create additional collections for team assembly workflow
3. Integrate end-to-end testing across both milestones
4. Add performance and load testing scenarios