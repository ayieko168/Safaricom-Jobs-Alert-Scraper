import requests
from datetime import datetime
import schedule
import time
import threading
import asyncio

from src.indexers import APIIndexer
from src.telegram_bot import run_bot, load_local_job, save_new_job, send_alert_message, SCRAPE_PERIODS

def get_data():
    print("Get New Data")
    
    # Get scraped jobs
    local_jobs_list = load_local_job()
        
    # Get the new jobs
    api_jobs_list = APIIndexer().get_jobs()['data']
    
    # Check for new jobs
    new_jobs_list = [job for job in api_jobs_list if job['job_id'] not in [job2['job_id'] for job2 in local_jobs_list]]
        
    # Update stored job jobs with the new ones ensuring unique ids
    local_jobs_list.extend(new_jobs_list)
    save_new_job(local_jobs_list)
    
    # Output new job entries
    if new_jobs_list:
        send_telegram_message("New jobs found:")
        for count, job in enumerate(new_jobs_list):
            datetime_obj = datetime.strptime(job['job_post_date'], "%Y-%m-%dT%H:%M:%S%z")
            current_date = datetime.now(datetime_obj.tzinfo)
            difference = current_date - datetime_obj
            
            message_str = f"{count+1}) {str(job['job_title']).upper()} - {job['job_location']} \n\n{job['job_short_description']} \n\n{difference.days} Days Ago. [link]({job['job_link']})\n"
                
            ## Send the message
            send_telegram_message(message_str, is_md=True)
            
        send_telegram_message("Done.")
    else:
        
        print("No new jobs found.")


def jobs_alert_scheduler():
    print("Running Jobs Alert Scheduler")
    
    schedule.every(SCRAPE_PERIODS).seconds.do(get_data)
    
    while True:
        schedule.run_pending()
        time.sleep(1)


def send_telegram_message(message, is_md=False):
    if is_md:
        asyncio.run(send_alert_message(message, is_md=True))
    else:
        asyncio.run(send_alert_message(message))


def main():
    
    ## Run the get data by indeexer thread
    indexer_thread = threading.Thread(target=jobs_alert_scheduler)
    indexer_thread.daemon = True
    indexer_thread.start()
    
    ## Run the tltgram bot thread
    print("Running Telegram Bot")
    run_bot()



if __name__ == "__main__":
    main()














