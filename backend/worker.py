#!/usr/bin/env python3
"""RQ worker script for background job processing."""

import sys
import logging
from app.jobs.worker_config import create_worker
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    """Run RQ worker."""
    try:
        logger.info("Starting RQ worker...")
        logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        logger.info(f"Queue: {settings.RQ_QUEUE_NAME}")
        
        # Create and start worker
        worker = create_worker()
        logger.info("Worker created successfully")
        
        # Start processing jobs
        worker.work()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()