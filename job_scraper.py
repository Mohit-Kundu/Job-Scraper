import json
import time
from datetime import datetime, timedelta
import pytz
import hashlib
from googlesearch import search
import schedule
import logging

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

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Convert time strings to datetime objects
        self.start_time = datetime.strptime(
            self.config['start_time'], 
            '%Y-%m-%d %H:%M:%S'
        )
        self.end_time = datetime.strptime(
            self.config['end_time'], 
            '%Y-%m-%d %H:%M:%S'
        )

    def setup_timezone(self):
        self.timezone = pytz.timezone(self.config['time_zone'])
        self.start_time = self.timezone.localize(self.start_time)
        self.end_time = self.timezone.localize(self.end_time)

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

    def search_jobs(self):
        """Perform the job search for all combinations"""
        current_time = datetime.now(self.timezone)
        
        # Check if we've passed the end time
        if current_time >= self.end_time:
            logging.info("Reached end time. Stopping the scraper.")
            return schedule.CancelJob

        # If this is our first run, look back to start_time
        if self.last_scrape_time is None:
            look_back_time = self.start_time
        else:
            # Otherwise, just look back one hour
            look_back_time = current_time - timedelta(hours=1)

        new_jobs_found = 0
        
        for job_title in self.config['job_titles']:
            for exp_level in self.config['experience']:
                search_query = (
                    f'site:lever.co OR site:greenhouse.io OR '
                    f'site:myworkdayjobs.com "{job_title}" "{exp_level}" '
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
                            logging.info(f"Title: {job_title} ({exp_level})")
                            logging.info(f"Link: {link}")
                            logging.info("-" * 50)

                    # Add delay to avoid hitting rate limits
                    time.sleep(2)

                except Exception as e:
                    logging.error(f"Error searching for {job_title}: {str(e)}")

        self.last_scrape_time = current_time
        logging.info(f"Scraping complete. Found {new_jobs_found} new jobs.")

    def run(self):
        """Start the scraper with scheduled runs"""
        # Run immediately on start
        self.search_jobs()
        
        # Schedule regular runs
        schedule.every(1).hours.do(self.search_jobs)
        
        # Keep running until end_time
        while datetime.now(self.timezone) < self.end_time:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    scraper = JobScraper()
    scraper.run() 