import pyttsx3
import speech_recognition as sr
import datetime
import webbrowser
import os
import sys
import wikipedia
import pyjokes
import requests
import queue
import sounddevice as sd
import vosk
import json
import threading 
#Initialize TTS engine

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Change index to select different voice
engine.setProperty('rate', 175)  # Set speech rate

model = vosk.Model("C:\Users\skcha\Python\vosk-model-small-en-us-0.15")
q = queue.Queue()

running = True

def speak(audio):
    print(f"dobby: {audio}")
    engine.say(audio)
    engine.runAndWait()

def greet_user():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("Hello Sir! Dobby here. Ready at your service.")

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase.")
            speak("I didn't catch that. Please say that again.")
            return None
       
    try:
        print("Recognizing...")
        command = r.recognize_google(audio, language='en-US')
        print(f"User said: {command}\n")
    except sr.UnknownValueError:
        print("Sorry, could not understand.")
        speak("Sorry, I didn't catch that. Could you please repeat?")
        return None
    except sr.RequestError:
        print("Could not request results from Google speech Recognition service.")
        speak("Sorry, I'm having trouble connecting to the internet.")
        return None
    
    return command.lower()

def tell_weather(city_name):
    api_key = "25b90e9154dddb40bf12bee883a9ddd1"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    full_url = base_url + "q=" + city_name + "&appid=" + api_key + "&units=metric"

    response = requests.get(full_url)
    weather_data = response.json()

    if weather_data["cod"] != "404":
        main = weather_data["main"]
        temp = main["temp"]
        pressure = main["pressure"]
        humidity = main["humidity"]
        speak(f"Temperature: {temp}°C")
        speak(f"Pressure: {pressure} hPa")
        speak(f"Humidity: {humidity}%")
    else:
        speak("City not found. Please check the name and try again.")

def calculator():
    try:
        command = command.replace('plus', '+')
        command = command.replace('minus', '-')
        command = command.replace('multiply', '*')
        command = command.replace('divide', '/')
        command = command.replace('power', '**')
        command = command.replace('square', '**2')
        command = command.replace('cube', '**3')
        result = eval(command)
        speak(f"The result is {result}")
    except Exception as e:
        speak("Sorry, I couldn't calculate that. Please try again.")

def search_job_role(command):
    try:
        if "search for" in command:
            #Extract job role
            role = command.split("search for")[-1].strip()
            speak(f"Searching LinkedIn for {role}")
            role_query = role.replace(" ", "+")
            url = f"https://www.linkedin.com/jobs/search/?keywords={role_query}"
            webbrowser.open(url)
    except Exception as e:
        speak("Sorry, something went wrong while searching LinkedIn.")
    
def run_dobby():
    greet_user()
    while True:
        command = take_command()
        if command is None:
            continue

        if 'wikipedia' in command:
            speak("Searching Wikipedia...")
            command = command.replace("wikipedia", "")
            result = wikipedia.summary(command, sentences=2)
            speak("According to Wikipedia")
            speak(result)

        elif 'open youtube' in command:
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")

        elif 'open google' in command:
            speak("Opening Google")
            webbrowser.open("https://www.google.com")

        elif 'time' in command:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            speak(f"The time is {strTime}")

        elif 'date' in command:
            today = datetime.date.today()
            speak(f"Today's date is {today}")

        elif 'tell me a joke' in command:
            joke = pyjokes.get_joke()
            speak(joke)

        elif 'weather' in command:
            speak("Please tell me the city name")
            city_name = take_command()
            if city_name:
                tell_weather(city_name)

        elif 'calculator' in command:
            speak("Please tell me the calculation")
            calc_query = take_command()
            if calc_query:
                calculator(calc_query)

        elif 'search for' in command:
            speak("Please tell me the job role")
            job_role = take_command()
            if job_role:
                search_job_role(job_role) 

        elif 'exit' in command or 'quit' in command or 'no thanks' in command or 'thanks buddy' in command or 'thank you' in command:
            speak("Goodbye Sir! shutting down.")
            sys.exit()

        else:
            speak("I do not understand that sir. Please try again.")

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def wake_word_listener():
    global running
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        print("Listening for wake word 'Hey Dobby'...")
        while running:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if "hey dobby" in text:
                    print("Wake word detected!")
                    speak("Yes Sir! How can I assist you?")
                    run_dobby()

if __name__ == "__main__":
    run_dobby()
    wake_word_listener()
