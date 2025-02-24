from googlesearch import search
import json
import time
import logging
import os
from datetime import datetime

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Set up logging configuration
    log_file = f'logs/demo_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # This will also print to console
        ]
    )
    return logging.getLogger(__name__)

def load_config(config_path='config/metadata.json'):
    with open(config_path, 'r') as f:
        return json.load(f)

def format_job_listing(job_number, job_title, result):
    """Format a job listing in a neat way"""
    separator = "=" * 80
    header = f"\nJob {job_number}:"
    title = f"Search Query: {job_title}"
    listing_title = f"Job Title: {result.title if result.title else 'N/A'}"
    url = f"URL: {result.url if result.url else 'N/A'}"
    description = f"Description: {result.description if result.description else 'N/A'}"
    
    return f"""
{separator}
{header}
{title}
{listing_title}
{url}
{description}
{separator}
"""

def scrape_jobs():
    logger = setup_logging()
    config = load_config()
    
    logger.info("🔍 Starting job search...")
    total_jobs_found = 0
    
    for job_title in config['job_titles']:
        logger.info(f"Searching for: {job_title}")
        
        search_query = (
            'site:lever.co OR site:greenhouse.io OR site:myworkdayjobs.com '
            f'"{job_title}"'
        )
        
        try:
            search_results = search(
                search_query,
                num_results=5,
                lang="en",
                region=config['region'],
                advanced=True,
                unique=True
            )
            
            jobs_found = 0
            for result in search_results:
                jobs_found += 1
                total_jobs_found += 1
                
                # Format and log the job listing
                job_listing = format_job_listing(jobs_found, job_title, result)
                logger.info(job_listing)
                
                # Add delay between searches to avoid rate limiting
                time.sleep(1)
            
            logger.info(f"Found {jobs_found} jobs for {job_title}")
            
            # Add longer delay between different job title searches
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error occurred while searching for {job_title}: {str(e)}")
            continue
    
    logger.info(f"Search complete. Total jobs found: {total_jobs_found}")

if __name__ == "__main__":
    scrape_jobs() 