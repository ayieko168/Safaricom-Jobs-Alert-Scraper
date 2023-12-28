from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import telegram
import os
import json
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import time
import asyncio

from .indexers import APIIndexer

load_dotenv()

ROOT_DIR = f'{os.sep}'.join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[:-1])
BOT_TOKEN = os.environ["BOT_TOKEN"]
SCRAPE_PERIODS = int(os.environ["SCRAPE_PERIODS"])
AUTH_RECIPIENTS = json.loads(os.environ["AUTH_RECIPIENTS"])
ALERT_RECIPIENTS = json.loads(os.environ["ALERT_RECIPIENTS"])
VISITOR_FILE = os.path.join(ROOT_DIR, 'src', 'visitors.json')
SCRAPED_JOBS_FILE = os.path.join(ROOT_DIR, 'src', 'job_ids.json')

interactions_ids = {}
# print(AUTH_RECIPIENTS, type(AUTH_RECIPIENTS))
# print(ROOT_DIR)
# print(BOT_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    await update.message.reply_text("Safaricom Jobs Alert Bot.\nUse /help to see available commands.")


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    help_str = f"""
    /start -> Start interaction with the bot.
    /help -> Show this help message.

    /jobs -> List all avaiable jobs.
    /sub -> Subscribe to daily alerts for available jobs.
    /unsub -> Un-subscribe from daily alerts for available jobs.
    
    /misctest
    """
    
    help_str = '\n'.join([s.strip() for s in help_str.split('\n')])
    help_str = "AVAILABE COMMANDS: \n" + help_str
    
    await update.message.reply_text(help_str)
    
    
async def list_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    await update.message.reply_text("Getting all available jobs...")
    
    ## Get all the available jobs
    response = APIIndexer().get_jobs()
    # print(response)
    jobs_list = response['data']
    
    ## Create message string
    for count, job in enumerate(jobs_list):
        datetime_obj = datetime.strptime(job['job_post_date'], "%Y-%m-%dT%H:%M:%S%z")
        current_date = datetime.now(datetime_obj.tzinfo)
        difference = current_date - datetime_obj
        
        message_str = f"{count+1}) {str(job['job_title']).upper()} - {job['job_location']} \n\n{job['job_short_description']} \n\n{difference.days} Days Ago. [link]({job['job_link']})\n"
            
        ## Send the message
        await update.message.reply_text(message_str, parse_mode=ParseMode.MARKDOWN)
    
    await update.message.reply_text("Done.")


async def subscribe_to_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    await update.message.reply_text("Subscribing to daily alerts for available jobs...")
        
    # Load the current values from the .env file
    env_values = dotenv_values('.env')
    
    # Update the specific key's value
    alert_recipients = json.loads(env_values['ALERT_RECIPIENTS'])
    alert_recipients.append(update.message.from_user.id)
    env_values['ALERT_RECIPIENTS'] = json.dumps(alert_recipients)
    
    # Write the updated values back to the .env file
    with open('.env', 'w') as f:
        for key, value in env_values.items():
            f.write(f'{key}=\"{value}\"\n')
            
    await update.message.reply_text("Done. You will recieve new job updates.")


async def un_subscribe_to_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    await update.message.reply_text("Un-subscribing from daily alerts for available jobs...")
    
    # Load the current values from the .env file
    env_values = dotenv_values('.env')
    
    # Update the specific key's value
    alert_recipients = json.loads(env_values['ALERT_RECIPIENTS'])
    alert_recipients.remove(update.message.from_user.id)
    env_values['ALERT_RECIPIENTS'] = json.dumps(alert_recipients)
    
    # Write the updated values back to the .env file
    with open('.env', 'w') as f:
        for key, value in env_values.items():
            f.write(f'{key}=\"{value}\"\n')
            
    await update.message.reply_text("Done. You will no longer recieve new job updates.")
    

async def list_visitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update)
    
    ## See if the inquiry comes from an authorized user
    req_user = update.message.from_user.id
    if req_user not in AUTH_RECIPIENTS:
        await update.message.reply_text("TEST OK")
        return
    
    ## Get the visitors
    with open(os.path.join(ROOT_DIR, 'src', 'visitors.json')) as fo:
        visitors_data = json.load(fo)
    
    ## Create message string
    message_str = ""
    for visitor in visitors_data.values():
        str_time = datetime.fromtimestamp(visitor['timestamp']).strftime("%a at %I:%S%p (%b %d %Y)")
        message_str += f"- {visitor['user_name']} on {str_time}"
    
    message_str = f"VISITORS:\n" + message_str

    ## Send the message
    await update.message.reply_text(message_str)


async def send_alert_message(message: str, is_md=False):
    
    bot = telegram.Bot(BOT_TOKEN)
    
    for user in ALERT_RECIPIENTS:
        async with bot:
            if is_md: 
                await bot.send_message(chat_id=user, text=message, parse_mode=ParseMode.MARKDOWN)
            else: 
                await bot.send_message(chat_id=user, text=message)
            

def log_user(update: Update):
    
    interactions_ids[update.message.from_user.id] = {
        'user_name': update.message.from_user.username,
        'timestamp': time.time()
    }
    
    print(f"[{datetime.now()}] Interaction with bot from user: {update.message.from_user.username}")
    
    with open(os.path.join(ROOT_DIR, 'src', 'visitors.json'), 'w') as fo: json.dump(interactions_ids, fo, indent=2)


def load_local_job():
    try:
        with open(SCRAPED_JOBS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_new_job(jobs_list):
    with open(SCRAPED_JOBS_FILE, 'w') as file:
        json.dump(jobs_list, file, indent=2)


def run_bot():
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", _help))
    app.add_handler(CommandHandler("jobs", list_jobs))
    app.add_handler(CommandHandler("sub", subscribe_to_alerts))
    app.add_handler(CommandHandler("unsub", un_subscribe_to_alerts))
    app.add_handler(CommandHandler("misctest", list_visitors))
    
    app.run_polling()
    

if __name__ == '__main__':
    run_bot()





























