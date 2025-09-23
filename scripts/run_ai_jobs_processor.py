#!/usr/bin/env python3

import os
import sys
import time
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_db
from src.background_service import process_pending_ai_jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_job_processor')

def main():
    """Main function to run the AI jobs processor."""
    logger.info("Starting AI Improvement Jobs processor")
    
    try:
        conn = get_db()
        
        while True:
            logger.info(f"Processing pending jobs at {datetime.now().isoformat()}")
            processed_count = process_pending_ai_jobs(conn)
            
            if processed_count > 0:
                logger.info(f"Processed {processed_count} job(s)")
            else:
                logger.info("No pending jobs found")
                
            # Sleep for a while before checking again
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Processor stopped by user")
    except Exception as e:
        logger.error(f"Error in job processor: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
