import telepot
import sys
import os
import time
import subprocess
from telepot.loop import MessageLoop
import tweepy
import wget
import speech_recognition as sr
import tokens as tok
import soundfile as sf
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
from googletrans import Translator

consumer_key = tok.consumer_key_twitter
consumer_secret = tok.consumer_secret_twitter
access_token = tok.access_token_twitter
access_token_secret = tok.access_token_secret_twitter

auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
TWEETS = []

r = sr.Recognizer()

TOKEN = tok.TOKEN_telegram
bot = telepot.Bot(TOKEN)

def handler(msg):
    msgType, chtType, chatId = telepot.glance(msg)
    if msg["text"] == "/listen":   
        bot.sendMessage(chatId,"A la espera de tweets...")  
        for tweet in api.mentions_timeline():
            status = tweet.text
            TWEETS.append(status)
        while True:
            time.sleep(10)
            for tweet in api.mentions_timeline():
                nombre = str("@"+tweet.user.screen_name)
                tweetId = tweet.id_str
                txtTweet = tweet.text
                cadena = str(nombre) + " Te ha mencionado en un tweet: "+ str(txtTweet)
                if not txtTweet in TWEETS:
                    TWEETS.append(txtTweet)
                    if hasattr(tweet,'extended_entities') and 'media' in tweet.extended_entities:
                        if "video_info" in tweet.extended_entities["media"][0] and "video" in tweet.extended_entities["media"][0]["type"]:
                            video = tweet.extended_entities["media"][0]["video_info"]["variants"][0]
                            video_url = video["url"]
                            audio = convertVideoToAudio(video_url)
                            text = transcribeAudio(audio, txtTweet)
                            api.update_status(nombre+' '+text, tweetId)
                            bot.sendMessage(chatId,"transripcion completada")
                            #bot.sendVideo(chatId,video_url) 
                        elif "additional_media_info" in tweet.extended_entities["media"][0] and "video" in tweet.extended_entities["media"][0]["type"]:
                            if(tweet.extended_entities["media"][0]["additional_media_info"]["embeddable"] == 1):
                                video = tweet.extended_entities["media"][0]["extended_entities"]["variants"][0]
                                video_url = video["url"]
                                audio = convertVideoToAudio(video_url)
                                text = transcribeAudio(audio, txtTweet)
                                api.update_status(nombre+' '+text, tweetId)
                                bot.sendMessage(chatId,"transripcion completada")
                            else:
                                api.update_status(nombre+' Media restricted by advertiser', tweetId)
                        else:
                            bot.sendMessage(chatId,cadena[0:-23])
                            num = len(tweet.extended_entities["media"])
                            for i in range(num):
                                media = tweet.extended_entities["media"][i]
                                media_url = media["media_url"]
                                bot.sendPhoto(chatId,media_url)
                    elif hasattr(tweet,'entities') and 'media' in tweet.entities:
                        media = tweet.entities["media"][0]
                        media_url = media["media_url"]
                        bot.sendMessage(chatId,cadena[0:-23])
                        bot.sendPhoto(chatId,media_url)
                    else:
                        bot.sendMessage(chatId,cadena)
                                           
    else:
        bot.sendMessage(chatId,"/listen")


def convertVideoToAudio(videoUrl):
    fileName = wget.download(videoUrl)
    print(fileName[0:-4])
    print(fileName[0:-4])
    shell_cmd = "ffmpeg -y -i {0} {1}.wav".format(fileName,fileName[0:-4])
    p = subprocess.Popen(shell_cmd, shell=True,stdout=subprocess.PIPE)
        
    while(p.wait() != 0):
        time.sleep(2)
    
    return fileName[0:-4]+".wav"

def transcribeAudio(audioFile, lang):
    with sr.AudioFile(audioFile) as source:
            # escuchando la data de la fuente
            audio_data = r.record(source)
            # reconocimiento (convirtiendo de voz a texto)
            text = r.recognize_google(audio_data) # r.recognize_google(audio_data,language="en")
            
            if lang in ("en","es","fr"):
                text = translateText(text, lang)

            return text

def translateText(text, lang):
    translator = Translator(service_urls=[
      'translate.google.com'
    ])

    translation = translator.translate(text, dest=lang)
    return translation


MessageLoop(bot,handler).run_as_thread()

while True:
    time.sleep(10)