import requests
from datetime import datetime
import schedule
import time
import threading
import asyncio
import telegram
from telegram.constants import ParseMode
import re

from src.indexers import APIIndexer
from src.telegram_bot import run_bot, load_local_job, save_new_job, send_alert_message, SCRAPE_PERIODS, BOT_TOKEN, ALERT_RECIPIENTS, AUTH_RECIPIENTS


def clean_text(raw_html):
    # Remove HTML tags
    # text = BeautifulSoup(raw_html, 'html.parser').get_text()

    # Remove extra spaces and unknown characters
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Replace non-breaking space with regular space
    text = text.replace('\xa0', ' ')

    return text.strip()





async def get_data():
    print("Getting New Data...")
    
    ## Create the bot
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Get scraped jobs
    local_jobs_list = load_local_job()
        
    # Get the new jobs
    api_jobs_list = APIIndexer().get_jobs()['data']
    
    # Check for new jobs
    new_jobs_list = [job for job in api_jobs_list if job['job_hash'] not in [job2['job_hash'] for job2 in local_jobs_list]]
        
    # Update stored job jobs with the new ones ensuring unique ids
    local_jobs_list.extend(new_jobs_list)
    save_new_job(local_jobs_list)
    
    # Output new job entries
    recipients = ALERT_RECIPIENTS + AUTH_RECIPIENTS
    recipients = list(set(recipients))
    async with bot:
        for user_id in recipients:
            if new_jobs_list:
                print(f"Sending new found {len(new_jobs_list)} jobs to recipients: {recipients}")
                await bot.send_message(chat_id=user_id, text="New jobs found:")
                for count, job in enumerate(new_jobs_list):
                    datetime_obj = datetime.strptime(job['job_post_date'], "%Y-%m-%dT%H:%M:%S%z")
                    current_date = datetime.now(datetime_obj.tzinfo)
                    difference = current_date - datetime_obj
                    
                    message_str = f"{count+1} {str(job['job_title']).upper()} - {job['job_location']} \n\n{job['job_short_description']} \n\n{difference.days} Days Ago. "
                    message_str += f"<a href='{job['job_link']}'> Apply here</a>"
                    # message_str = clean_text(message_str)
                    print(message_str)
                        
                    ## Send the message
                    await bot.send_message(chat_id=user_id, text=message_str, parse_mode=ParseMode.HTML)
                    
            else:
                print("No new jobs found.")


def jobs_alert_scheduler():
    print("Running Jobs Alert Scheduler")
    
    schedule.every(SCRAPE_PERIODS).seconds.do(lambda: asyncio.run(get_data()))
    
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
    
    ## Run the telegram bot thread
    print("Running Telegram Bot")
    run_bot()



if __name__ == "__main__":
    main()














