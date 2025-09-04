import os
from shlex import quote
import sqlite3
import struct
import subprocess
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from hugchat import hugchat
from playsound import playsound
import eel
import re
import pyaudio

import pvporcupine
import time

import pyautogui
from engine.command import speak
from engine.config import ASSISTANT_NAME
import pywhatkit as kit

from engine.helper import extract_yt_term, remove_words

con = sqlite3.connect("jarvis.db")
cursor=con.cursor()


# Spotify API credentials
SPOTIFY_CLIENT_ID = "2bffbec487ec45e8ab79bffe7a7ab1d7"       # Replace with your Client ID
SPOTIFY_CLIENT_SECRET = "ebf3acc3ff09443c9552a99de50e4118" # Replace with your Client Secret
SPOTIFY_REDIRECT_URI = "http://localhost:8000/index.html"  # Your redirect URI

# Authenticate the user
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))

#playing assistant sound function
@eel.expose
def playAssistantSound():
    music_dir="www\\assests\\audio\\mic_sound.mp3"
    playsound(music_dir)

def openCommand(query):
    query=query.replace(ASSISTANT_NAME,"")
    query=query.replace("open","")
    print(query.lower())

    app_name = query.strip()

    if app_name != "":

        try:
            cursor.execute(
                'SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening "+query)
                os.startfile(results[0][0])

            elif len(results) == 0: 
                cursor.execute(
                'SELECT url FROM web_command WHERE name IN (?)', (app_name,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    speak("Opening "+query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening "+query)
                    try:
                        os.system('start '+query)
                    except:
                        speak("not found")
        except:
            speak("some thing went wrong")


def PlayYoutube(query):
    search_term=extract_yt_term(query)
    speak("Playing "+search_term+ "on YouTube")
    kit.playonyt(search_term)

def PlaySpotify(song_name):
    import webbrowser
    base_url = "https://open.spotify.com/search/"
    webbrowser.open(base_url + song_name.replace(" ", "%20"))

# Function to open Spotify search in the browser
def open_spotify(song_name):
    import webbrowser
    base_url = "https://open.spotify.com/search/"
    webbrowser.open(base_url + song_name.replace(" ", "%20"))

# Function to play a song on Spotify
def PlaySpotify(query):
    from engine.helper import extract_yt_term  # Reuse your helper function
    song_name = extract_yt_term(query)  # Extract song name from the query
    if song_name:
        speak(f"Searching for {song_name} on Spotify")
        open_spotify(song_name)  # Open Spotify in the browser
    else:
        speak("I couldn't understand the song name.")

def play_on_spotify(song_name): 
    try:
        # Search for the song
        results = sp.search(q=song_name, limit=1, type='track')
        if results['tracks']['items']:
            song_uri = results['tracks']['items'][0]['uri']
            song_title = results['tracks']['items'][0]['name']
            artist = results['tracks']['items'][0]['artists'][0]['name']

            # Check for active devices
            devices = sp.devices()
            if devices['devices']:
                device_id = devices['devices'][0]['id']  # Select the first active device
                sp.start_playback(device_id=device_id, uris=[song_uri])
                speak(f"Playing {song_title} by {artist} on Spotify.")
            else:
                # Open in browser if no active device
                webbrowser.open(results['tracks']['items'][0]['external_urls']['spotify'])
                speak(f"No active devices found. Opening {song_title} by {artist} in your browser.")
        else:
            speak("Sorry, I couldn't find the song on Spotify.")
    except Exception as e:
        print(f"Error playing on Spotify: {e}")
        speak("Something went wrong while trying to play the song on Spotify.")

def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
       
        # pre trained keywords    
        porcupine=pvporcupine.create(keywords=["jarvis","alexa"]) 
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        # loop for streaming
        while True:
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)

            # processing keyword comes from mic 
            keyword_index=porcupine.process(keyword)

            # checking first keyword detetcted for not
            if keyword_index>=0:
                print("hotword detected")

                # pressing shorcut key win+j
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
                
    except:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


# find contacts
def findContact(query):
    
    
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])
        if not mobile_number_str.startswith('+91'):
            mobile_number_str = '+91' + mobile_number_str

        return mobile_number_str, query
    except:
        speak('not exist in contacts')
        return 0, 0


def whatsApp(mobile_no, message, flag, name):

    if flag == 'message':
        target_tab = 12
        jarvis_message = "message send successfully to "+name

    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = "calling to "+name

    else:
        target_tab = 6
        message = ''
        jarvis_message = "staring video call with "+name

    # Encode the message for URL
    encoded_message = quote(message)

    # Construct the URL
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Construct the full command
    full_command = f'start "" "{whatsapp_url}"'

    # Open WhatsApp with the constructed URL using cmd.exe
    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)
    
    pyautogui.hotkey('ctrl', 'f')

    for i in range(1, target_tab):
        pyautogui.hotkey('tab')

    pyautogui.hotkey('enter')
    speak(jarvis_message)

#chatbot
def chatBot(query):
    try:
        user_input = query.lower().strip()
        print(user_input)
        chatbot = hugchat.ChatBot(cookie_path="engine\\cookies.json")
        id = chatbot.new_conversation()
        chatbot.change_conversation(id)
        
        # Process the response
        response = chatbot.chat(user_input)
        print(f"Response: {response}")
        speak(response)
        return response
    except Exception as e:
        print(f"Error during chatBot: {e}")
        speak("Sorry, I encountered an error processing your request.")
        return "Error"



# import os
# from pipes import quote
# import re
# import sqlite3
# import struct
# import subprocess
# import time
# import webbrowser
# from playsound import playsound
# import eel
# import pyaudio
# import pyautogui
# from engine.command import speak
# from engine.config import ASSISTANT_NAME
# # Playing assiatnt sound function
# import pywhatkit as kit
# import pvporcupine

# from engine.helper import extract_yt_term, remove_words
# from hugchat import hugchat

# con = sqlite3.connect("jarvis.db")
# cursor = con.cursor()

# @eel.expose
# def playAssistantSound():
#     music_dir = "www\\assets\\audio\\start_sound.mp3"
#     playsound(music_dir)

    
# def openCommand(query):
#     query = query.replace(ASSISTANT_NAME, "")
#     query = query.replace("open", "")
#     query.lower()

#     app_name = query.strip()

#     if app_name != "":

#         try:
#             cursor.execute(
#                 'SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
#             results = cursor.fetchall()

#             if len(results) != 0:
#                 speak("Opening "+query)
#                 os.startfile(results[0][0])

#             elif len(results) == 0: 
#                 cursor.execute(
#                 'SELECT url FROM web_command WHERE name IN (?)', (app_name,))
#                 results = cursor.fetchall()
                
#                 if len(results) != 0:
#                     speak("Opening "+query)
#                     webbrowser.open(results[0][0])

#                 else:
#                     speak("Opening "+query)
#                     try:
#                         os.system('start '+query)
#                     except:
#                         speak("not found")
#         except:
#             speak("some thing went wrong")

       

# def PlayYoutube(query):
#     search_term = extract_yt_term(query)
#     speak("Playing "+search_term+" on YouTube")
#     kit.playonyt(search_term)


# def hotword():
#     porcupine=None
#     paud=None
#     audio_stream=None
#     try:
       
#         # pre trained keywords    
#         porcupine=pvporcupine.create(keywords=["jarvis","alexa"]) 
#         paud=pyaudio.PyAudio()
#         audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
#         # loop for streaming
#         while True:
#             keyword=audio_stream.read(porcupine.frame_length)
#             keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)

#             # processing keyword comes from mic 
#             keyword_index=porcupine.process(keyword)

#             # checking first keyword detetcted for not
#             if keyword_index>=0:
#                 print("hotword detected")

#                 # pressing shorcut key win+j
#                 import pyautogui as autogui
#                 autogui.keyDown("win")
#                 autogui.press("j")
#                 time.sleep(2)
#                 autogui.keyUp("win")
                
#     except:
#         if porcupine is not None:
#             porcupine.delete()
#         if audio_stream is not None:
#             audio_stream.close()
#         if paud is not None:
#             paud.terminate()



# # find contacts
# def findContact(query):
    
#     words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
#     query = remove_words(query, words_to_remove)

#     try:
#         query = query.strip().lower()
#         cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
#         results = cursor.fetchall()
#         print(results[0][0])
#         mobile_number_str = str(results[0][0])

#         if not mobile_number_str.startswith('+91'):
#             mobile_number_str = '+91' + mobile_number_str

#         return mobile_number_str, query
#     except:
#         speak('not exist in contacts')
#         return 0, 0
    
# def whatsApp(mobile_no, message, flag, name):
    

#     if flag == 'message':
#         target_tab = 12
#         jarvis_message = "message send successfully to "+name

#     elif flag == 'call':
#         target_tab = 7
#         message = ''
#         jarvis_message = "calling to "+name

#     else:
#         target_tab = 6
#         message = ''
#         jarvis_message = "staring video call with "+name


#     # Encode the message for URL
#     encoded_message = quote(message)
#     print(encoded_message)
#     # Construct the URL
#     whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

#     # Construct the full command
#     full_command = f'start "" "{whatsapp_url}"'

#     # Open WhatsApp with the constructed URL using cmd.exe
#     subprocess.run(full_command, shell=True)
#     time.sleep(5)
#     subprocess.run(full_command, shell=True)
    
#     pyautogui.hotkey('ctrl', 'f')

#     for i in range(1, target_tab):
#         pyautogui.hotkey('tab')

#     pyautogui.hotkey('enter')
#     speak(jarvis_message)

# # chat bot 
# def chatBot(query):
#     user_input = query.lower()
#     chatbot = hugchat.ChatBot(cookie_path="engine\\_pycache_\\cookies.json")
#     id = chatbot.new_conversation()
#     chatbot.change_conversation(id)
#     response =  chatbot.chat(user_input)
#     print(response)
#     speak(response)
#     return response

# # android automation

# def makeCall(name, mobileNo):
#     mobileNo =mobileNo.replace(" ", "")
#     speak("Calling "+name)
#     command = 'adb shell am start -a android.intent.action.CALL -d tel:'+mobileNo
#     os.system(command)


# # to send message
# def sendMessage(message, mobileNo, name):
#     from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
#     message = replace_spaces_with_percent_s(message)
#     mobileNo = replace_spaces_with_percent_s(mobileNo)
#     speak("sending message")
#     goback(4)
#     time.sleep(1)
#     keyEvent(3)
#     # open sms app
#     tapEvents(136, 2220)
#     #start chat
#     tapEvents(819, 2192)
#     # search mobile no
#     adbInput(mobileNo)
#     #tap on name
#     tapEvents(601, 574)
#     # tap on input
#     tapEvents(390, 2270)
#     #message
#     adbInput(message)
#     #send
#     tapEvents(957, 1397)
#     speak("message send successfully to "+name)