#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import re
import os
import urllib
import subprocess
import cfscrape
import botan

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters

import logging
import datetime

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi! Send me webm.')


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='I love webms. Send me one and I\'ll make it playable here.')


def escape_markdown(text):
    """Helper function to escape telegram markup symbols"""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)


def check_url(text):
    text = text.replace('@webmvid_bot', '')
    text = text.strip()

    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    m = regex.match(text)
    if m:
        return text

    return False


def convert(filename):
    command = "ffmpeg -y -i files/" + filename + ".webm -strict experimental files/" + filename + ".mp4"
    #print command
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return True

def download(url):
    dt = datetime.datetime.now()
    uploaded_file_name = dt.strftime('%Y%m%d%-H%M%S%f')
    uploaded_webm_name = "files/" + dt.strftime('%Y%m%d%-H%M%S%f') + ".webm"
    
    scraper = cfscrape.create_scraper(js_engine="Node")  # returns a CloudflareScraper instance
    content = scraper.get(url).content
        
    with open(uploaded_webm_name, 'w') as f:
        f.write(content)
                    
    return uploaded_file_name
    #filename, headers = urllib.urlretrieve (url, uploaded_webm_name)
    #print headers
    #if headers['Content-Type'] == 'video/webm':
    #    return uploaded_file_name
    #else:
    #    return False

def convert_webm(bot, update):
    url = check_url(update.message.text)
    
    botan_token = '<<botan_token>>'
    uid = update.message.chat_id
    message_dict = update.message.to_dict()
    event_name = update.message.text
    print botan.track(botan_token, uid, message_dict, event_name)
    
    error = 'No error is error too'
    if url:
        #if uploaded_file_name = download(url):
        uploaded_file_name = download(url)

        if uploaded_file_name:
            if convert(uploaded_file_name):
                video_file = open('files/' + uploaded_file_name+'.mp4', 'rb')
                print bot.sendVideo(update.message.chat_id, video=video_file)
                #print "The dir is: %s" %os.listdir(os.getcwd())
                os.remove('files/' + uploaded_file_name + '.webm')
                os.remove('files/' + uploaded_file_name + '.mp4')
                return True
            else:
                error = 'Error converting. Terribly sorry.'
        else:
            error = 'Error downloading. Sorry.'
    else:
        error = 'Please send valid webm url. https://example.com/video.webm'

    bot.sendMessage(update.message.chat_id, error)

    return error

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the Updater and pass it your bot's token.
            
    updater = Updater("<<ID:token here >>")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.addHandler(CommandHandler("start", start))
    dp.addHandler(CommandHandler("help", help))

    dp.addHandler(MessageHandler([Filters.text], convert_webm))

    # on noncommand i.e message - echo the message on Telegram
    #dp.addHandler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
