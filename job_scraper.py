import json
import time
from datetime import datetime, timedelta
import pytz
import hashlib
from googlesearch import search
import schedule
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class JobScraper:
    def __init__(self, config_path='config/metadata.json'):
        self.seen_jobs = set()  # Store hashes of seen jobs
        self.load_config(config_path)
        self.setup_timezone()
        self.last_scrape_time = None  # Track when we last scraped
        
        # Set up logging
        self.setup_logging()

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Convert time strings to time objects
        self.start_time = datetime.strptime(
            self.config['start_time'], 
            '%H:%M:%S'
        ).time()
        
        self.end_time = datetime.strptime(
            self.config['end_time'], 
            '%H:%M:%S'
        ).time()

    def setup_timezone(self):
        self.timezone = pytz.timezone(self.config['time_zone'])

    def generate_job_hash(self, title, link):
        """Generate a unique hash for a job based on its title and link"""
        job_string = f"{title.lower()}{link.lower()}"
        return hashlib.md5(job_string.encode()).hexdigest()

    def is_new_job(self, title, link):
        """Check if we've seen this job before"""
        job_hash = self.generate_job_hash(title, link)
        if job_hash in self.seen_jobs:
            return False
        self.seen_jobs.add(job_hash)
        return True

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up logging configuration
        log_file = f'logs/job_scraper_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # This will also print to console
            ]
        )
        self.logger = logging.getLogger(__name__)

    def search_jobs(self):
        self.logger.info("Starting job search...")
        current_time = datetime.now(self.timezone)
        
        # If this is our first run, look back from start_time to current_time
        if self.last_scrape_time is None:
            # Get today's start time
            today = current_time.date()
            start_datetime = datetime.combine(today, self.start_time)
            start_datetime = self.timezone.localize(start_datetime)
            
            # Use start_time as look_back if current_time is after start_time
            # Otherwise use previous day's start_time
            if current_time >= start_datetime:
                look_back_time = start_datetime
            else:
                yesterday = today - timedelta(days=1)
                look_back_time = datetime.combine(yesterday, self.start_time)
                look_back_time = self.timezone.localize(look_back_time)
        else:
            # Otherwise, just look back one hour from current_time
            look_back_time = current_time - timedelta(hours=1)

        new_jobs_found = 0
        
        for job_title in self.config['job_titles']:
            search_query = (
                f'site:lever.co OR site:greenhouse.io OR '
                f'site:myworkdayjobs.com "{job_title}" '
                f'after:{int(look_back_time.timestamp())}'
            )
            
            try:
                # Search Google
                search_results = search(
                    search_query,
                    num_results=10,  # Adjust as needed
                    lang="en"
                )

                # Process results
                for link in search_results:
                    if self.is_new_job(job_title, link):
                        new_jobs_found += 1
                        logging.info(f"New Job Found:")
                        logging.info(f"Title: {job_title}")
                        logging.info(f"Link: {link}")
                        logging.info("-" * 50)

                # Add delay to avoid hitting rate limits
                time.sleep(2)

            except Exception as e:
                logging.error(f"Error searching for {job_title}: {str(e)}")

        self.last_scrape_time = current_time
        logging.info(f"Scraping complete. Found {new_jobs_found} new jobs.")

    def is_within_operating_hours(self):
        # Get current time in configured timezone
        current_time = datetime.now(self.timezone).time()
        
        self.logger.debug(f"Current time: {current_time}")
        
        # Check if current time is within operating hours
        return self.start_time <= current_time <= self.end_time

    def run(self):
        self.logger.info("Job scraper started")
        # Schedule the job to run at the specified frequency
        schedule.every(1).hours.do(self.search_jobs)
        
        while True:
            if self.is_within_operating_hours():
                schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    scraper = JobScraper()
    scraper.run() 