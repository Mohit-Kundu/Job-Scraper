from googlesearch import search
import time

def scrape_entry_level_jobs():
    # Search query for entry level software jobs
    search_query = (
        'site:lever.co OR site:greenhouse.io OR site:myworkdayjobs.com '
        '"entry level software engineer" OR "entry level software developer" OR "software engineer new grad"'
    )
    
    print("🔍 Searching for entry-level software jobs...\n")
    
    try:
        # Get search results
        search_results = search(
            search_query,
            num_results=10,
            lang="en"
        )
        
        # Print results
        for i, link in enumerate(search_results, 1):
            print(f"Job {i}:")
            print(f"Link: {link}")
            print("-" * 50)
            
            # Add delay between searches to avoid rate limiting
            time.sleep(1)
            
    except Exception as e:
        print(f"Error occurred while searching: {str(e)}")

if __name__ == "__main__":
    scrape_entry_level_jobs() 