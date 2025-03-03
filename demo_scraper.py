from googlesearch import search
import json
import time
import logging
import os
from datetime import datetime
import hashlib
import pickle

class JobCache:
    def __init__(self, cache_file='cache/jobs.pkl', max_size=100000):
        self.cache_file = cache_file
        self.max_size = max_size  # Maximum number of entries
        self.cache = self.load_cache()
        
    def load_cache(self):
        """Load cache from file or create new if doesn't exist"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        return set()
    
    def save_cache(self):
        """Save cache to file"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def generate_job_hash(self, title, url, description):
        """Generate a unique hash for a job"""
        job_string = f"{title.lower()}{url.lower()}{description.lower()}"
        return hashlib.md5(job_string.encode()).hexdigest()
    
    def cleanup_old_entries(self):
        """Remove oldest entries if cache exceeds max size"""
        if len(self.cache) > self.max_size:
            # Convert to list to remove oldest entries (first entries)
            as_list = list(self.cache)
            self.cache = set(as_list[-self.max_size:])
            self.save_cache()
            
    def is_duplicate(self, title, url, description):
        """Check if job is a duplicate"""
        job_hash = self.generate_job_hash(title, url, description)
        if job_hash in self.cache:
            return True
        self.cache.add(job_hash)
        self.cleanup_old_entries()  # Check size and cleanup if needed
        self.save_cache()
        return False

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
    """Format a job listing to a readable format"""
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
    job_cache = JobCache()
    
    logger.info("🔍 Starting job search...")
    total_jobs_found = 0
    total_duplicates = 0
    
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
            duplicates = 0
            
            for result in search_results:
                # Check if job is duplicate
                if job_cache.is_duplicate(
                    result.title or '',
                    result.url or '',
                    result.description or ''
                ):
                    duplicates += 1
                    total_duplicates += 1
                    logger.debug(f"Duplicate job found: {result.url}")
                    continue
                
                jobs_found += 1
                total_jobs_found += 1
                
                # Format and log the job listing
                job_listing = format_job_listing(jobs_found, job_title, result)
                logger.info(job_listing)
                
                # Add delay between searches to avoid rate limiting
                time.sleep(1)
            
            logger.info(f"Found {jobs_found} new jobs and {duplicates} duplicates for {job_title}")
            
            # Add longer delay between different job title searches
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error occurred while searching for {job_title}: {str(e)}")
            continue
    
    logger.info(f"Search complete. Total new jobs found: {total_jobs_found}")
    logger.info(f"Total duplicate jobs skipped: {total_duplicates}")

if __name__ == "__main__":
    scrape_jobs() 