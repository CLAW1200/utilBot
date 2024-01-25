import os
import random
import logging
import time
import toml
from PIL import Image, ImageSequence, ImageChops
import requests
import json
import datetime
from bs4 import BeautifulSoup
import shutil
import subprocess
import hashlib
import csv
import dateutil.parser
from matplotlib import pyplot as plt
from difflib import SequenceMatcher
from qrcode import QRCode, constants
from numpy import array
import aiohttp
import aiofiles
from playwright.async_api import async_playwright

# Create a log
log = logging.getLogger('Utility Belt Lib')
log.setLevel(logging.DEBUG)

# Create a formatter and set it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('data/app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)

def log_guild_message(message):
    # Get the server name and channel name
    server_name = message.guild.name
    channel_name = message.channel.name
    #get the time in GMT
    time_code = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the directory if it doesn't exist
    directory = f"guilds/{message.guild.id}"
    os.makedirs(directory, exist_ok=True)
    
    # Create the file path
    file_path = f"{directory}/{message.channel.id}.txt"
    
    # Write the server name and channel name to the file
    with open(file_path, "a", encoding="utf-8") as file:
        # Write the server name and channel name if the file is empty
        if file.tell() == 0:
            file.write(f"Server: {server_name}\n")
            file.write(f"Channel: {channel_name}\n")
        
        # Format the message information
        author_info = f"{message.author.name}#{message.author.discriminator} ({message.author.id})"
        attachments_info = f"Attachments: {', '.join(str(attachment) for attachment in message.attachments)}"
        embeds_info = f"Embeds: {', '.join(str(embed) for embed in message.embeds)}"
        
        # Write the formatted message to the file
        file.write(f"{author_info}:\n")
        file.write(f"Time (GMT): {time_code}\n")
        file.write(f"Message: {message.content}\n")
        file.write(f"{attachments_info}\n")
        file.write(f"{embeds_info}\n")
        file.write("--------------------------------\n")


def get_tokens(tokenFile):
    with open(tokenFile) as toml_file:
        data = toml.load(toml_file)
        bot_token = data["tokenLive"]
        top_gg_token = data["top-gg-token"]
        return bot_token, top_gg_token

def edit_user_data(user, field, data):
    # Edit data/users.json, add data to key
    user_id = str(user.id)
    try:
        with open("data/users.json", "r+") as f:
            users = json.load(f)
            if user_id in users:
                user_data = users[user_id]
                user_data[field] = data
            else:
                user_data = {field: data}
            users[user_id] = user_data
            f.seek(0)
            json.dump(users, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        users = {user_id: {field: data}}
        with open("data/users.json", "w") as f:
            json.dump(users, f, indent=4)

def add_user_data(user, field, data):
    # Edit data/users.json, add data to key if it doesn't exist
    user_id = str(user.id)
    try:
        with open("data/users.json", "r+") as f:
            users = json.load(f)
            if user_id in users:
                user_data = users[user_id]
                if field not in user_data:
                    user_data[field] = data
            else:
                user_data = {field: data}
                users[user_id] = user_data
            f.seek(0)
            json.dump(users, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        users = {user_id: {field: data}}
        with open("data/users.json", "w") as f:
            json.dump(users, f, indent=4)

def get_user_data(user, field):
    # Get data from data/users.json
    user_id = str(user.id)
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
            if user_id in users:
                user_data = users[user_id]
                return user_data.get(field, 0)
            else:
                return 0
    except FileNotFoundError:
        return 0
    
def get_user_id(username):
    # get a user id from a username and discriminator
    # lookup username and discriminator in data/users.json
    with open("data/users.json", "r") as f:
        users = json.load(f)
        for user_id in users:
            user_data = users[user_id]
            if user_data["username"] == username:
                return user_id

def zip_archive_folder(folder):
    shutil.make_archive('guilds', 'zip', 'guilds')
    return f"{folder}.zip"
   
def read_log():
    log.debug("Reading log")
    with open("data/app.log", "r") as f:
        return f.read()
    
def clear_log():
    open("data/app.log", "w").close()
    log.debug("Log cleared")

def read_toml_var(var):
    log.debug(f"Reading variable '{var}' from config")
    configFile = "config/config.toml"
    with open(configFile) as toml_file:
        data = toml.load(toml_file)
        log.debug(f"Variable '{var}' read from '{configFile}'")
        return data[var]

def clean_up_temp_files():
    log.debug("Checking for old files")
    for file in os.listdir("temp"):
        if os.path.getmtime(f"temp/{file}") < time.time() - (5 * 60): # 5 minutes
            try:
                os.remove(f"temp/{file}")
                log.debug(f"Removed old file '{file}'")
            except Exception as e:
                log.error(f"Error removing old file '{file}': {e}")

def get_file_size(link):
    # function to check the size of a video or image link
    try:
        response = requests.head(link)
        file_size = int(response.headers.get('content-length', 0))
        return file_size
    except Exception as e:
        log.error(f"Error getting file size for '{link}': {e}")
        return None

def download_check(link, max_size=read_toml_var("maxFileSize")):
    # function to check if a file is too large to download
    # if the file is too large, return false
    # if the file is small enough, return true
    # if the file size cannot be determined, return true
    file_size = get_file_size(link)
    if file_size is None:
        return False
    else:
        if file_size > max_size:
            log.warning(f"File '{link}' is too large to download ({file_size} > {max_size})")
            return False
        else:
            return True

def split_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    for frame in ImageSequence.Iterator(gif):
        frame = frame.convert('RGBA')
        frames.append(frame.copy())
    return frames

def link_processor(link):
    response = requests.get(link)
    if response.status_code == 200:
        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        meta_tag = soup.find('meta', attrs={'property': 'og:image'})
        if meta_tag:
            return meta_tag['content']
        else:
            return link
    else:
        return link
    
def convert_image_to_gif(image_link):
    image_link = link_processor(image_link)
    clean_up_temp_files()
    # this function will take a link to an image and convert it to a gif by simply changing the extension
    #if image link is sent, download image in temp folder
    if download_check(image_link):
        data = requests.get(image_link).content # download image
    image_seed = hashlib.md5(data).hexdigest() # generate a unique seed for the image based on its content
    # if the image is already in the temp folder, don't download it again
    if os.path.isfile(f"temp/{image_seed}.gif"):
        log.info(f"Image '{image_link}' already converted to gif '{image_seed}.gif'")
        output_path = f"temp/{image_seed}.gif"
        return output_path
    else:
        try:
            with open(f"temp/{image_seed}.png", "wb") as f: # save image in temp folder
                f.write(data) # write image data to file
        except FileExistsError as e:
            log.error(f"Error saving image '{image_link}' to temp folder: {e}")
            pass
        output_path = f"temp/{image_seed}.gif" # set output path
        os.rename(f"temp/{image_seed}.png", f"temp/{image_seed}.gif") # rename image to gif
        log.info(f"Converted image '{image_link}' to gif '{output_path}'")
        return output_path

def convert_video_to_gif(video_link, fps=25, scale = None):
    video_link = link_processor(video_link)
    clean_up_temp_files()
    #this function will take a link to an video and convert it to a gif
    #download video in temp folder
    #check file size
    # make sure file size is less than max
    if download_check(video_link):
        data = requests.get(video_link).content # download image
    video_seed = hashlib.md5(data).hexdigest() # generate a unique seed for the image based on its content
    #download video in temp folder
    with open(f"temp/{video_seed}", "wb") as f:
        f.write(data)
    # Open the Video file and convert to gif in good quality
    try:
        # ffmpeg -i input.mp4 -filter_complex "[0:v] fps=fps,scale=480:-1,split [a][b];[a] palettegen [p];[b][p] paletteuse" output.gif
        if scale is None:
            scale = "scale=480:-1"
        else:
            scale = f"scale={scale}:-1"

        output_path = f"temp/{video_seed}.gif"
        subprocess.call(['ffmpeg', '-n', '-i', f"temp/{video_seed}", '-filter_complex', f'[0:v] fps=fps={fps},{scale},split [a][b];[a] palettegen [p];[b][p] paletteuse', output_path])
        os.remove(f"temp/{video_seed}")
        log.info(f"Converted video '{video_link}' to gif '{output_path}'")
        return output_path
    except Exception as e:
        log.error(f"Error converting video '{video_link}' to gif: {e}")
        return None

def add_speech_bubble(image_link, speech_bubble_y_scale):
    image_link = link_processor(image_link)
    clean_up_temp_files()
    """
    Add a speech bubble to the top of the image or each frame of a GIF.
    """
    if download_check(image_link):
        data = requests.get(image_link).content

    image_seed = hashlib.md5(data).hexdigest()
    speechBubble = "assets/speechBubble.png"
    output_path = f"temp/{image_seed}.gif"

    with open(output_path, "wb") as f:
        f.write(data)
        
    # Load the gif and speech bubble
    image = Image.open(output_path).convert("RGBA")
    bubble = Image.open(speechBubble).convert("RGBA")

    # Calculate 20% of the height of the first image
    new_height = int(image.height * speech_bubble_y_scale)

    # Resize the speech bubble to exactly 20% of the image's height and 100% of the image's width
    bubble = bubble.resize((image.width, new_height))

    # Create a new GIF with the speech bubble on top of each frame
    input_frames = split_gif_frames(output_path)
    output_frames = []
    for input_frame in input_frames:
        # Create a new image with the same size as the original image
        result = Image.new("RGBA", input_frame.size) # A blank image with the same size as the original
        # Paste the resized speech bubble onto the new image at the top left corner (0,0)
        result.paste(bubble, (0,0), bubble) # Paste the bubble onto the blank image

        # Result now contains the speech bubble on top of the blank image
        # Frame now contains the original frame
        frame = ImageChops.composite(result, input_frame, result)
        # Now remove the speech bubble from the original frame and make it transparent
        frame = ImageChops.subtract(input_frame, result)
        output_frames.append(frame)

    # Save the result
    try:
        output_frames[0].save(output_path, save_all=True, append_images=output_frames[1:], duration=image.info['duration'], loop=0)
    # except for GIFs with no duration
    except KeyError:
        output_frames[0].save(output_path, save_all=True, append_images=output_frames[1:])
    return output_path


def gif_search(query):
    tokenFile = "config/token.toml"
    with open(tokenFile) as toml_file:
        data = toml.load(toml_file)
        GIPHY_API_KEY = data["giphy-api-key"]
    # Create the search URL based on the query
    url = "http://api.giphy.com/v1/gifs/search?"
    params = {
        "api_key": GIPHY_API_KEY,
        "q": query,
        "limit": 1,
        "offset": random.randint(1, 100),
        "rating": "g",
        "lang": "en"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if len(data['data']) > 0:
            # Return the first GIF's URL
            return data['data'][0]['images']['original']['url']
        else:
            print('No GIFs found.')
            gif_search(query)
    else:
        print('Failed to get a response from the API.')
        return

def status(status):
    #open config toml and set status to string
    configFile = "config/config.toml"
    with open(configFile) as toml_file:
        data = toml.load(toml_file)
        data["status"] = status
    #write toml file
    with open(configFile, "w") as toml_file:
        toml.dump(data, toml_file)

def search(mode, query):
    """Conduct a full search for either message or user."""
    if mode == "message":
        # Search through all text files in /guilds/ for query
        def search_text_files(directory, search_string):
            matching_lines = []
            
            # Iterate through all files in the directory
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".txt"):
                        file_path = os.path.join(root, file)
                        
                        # Open the file and search for the string
                        with open(file_path, 'r', encoding="UTF-8") as f:
                            lines = f.readlines()
                            for line_number, line in enumerate(lines):
                                if search_string.lower() in line:
                                    matching_lines.append((line.strip(), file_path, line_number))
            
            return matching_lines
        
        with open("temp/search.txt", "w", encoding="UTF-8") as f:
            f.write(f"Search results for '{query}':\n\n")
            for result in search_text_files("guilds", query):
                f.write(f"{result[0]}\n({result[1]}:{result[2]})\n\n")
    
    elif mode == "user":
        # Search through all text files in /guilds/ for query between two lines of "--------------------------------"
        def search_user_files(directory, search_string):
            matching_lines = []
            
            # Iterate through all files in the directory
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".txt"):
                        file_path = os.path.join(root, file)
                        
                        # Open the file and search for the string between two lines of "--------------------------------"
                        with open(file_path, 'r', encoding="UTF-8") as f:
                            lines = f.readlines()
                            start_line = None
                            for line_number, line in enumerate(lines):
                                if line.strip() == "--------------------------------":
                                    if start_line is None:
                                        start_line = line_number
                                    else:
                                        end_line = line_number
                                        break
                            if start_line is not None and end_line is not None:
                                # Process lines between start_line and end_line
                                for i in range(start_line + 1, end_line):
                                    if search_string.lower() in lines[i]:
                                        matching_lines.append((lines[i].strip(), file_path, i))
            
            return matching_lines
        
        with open("temp/search.txt", "w", encoding="UTF-8") as f:
            f.write(f"Search results for '{query}' (User Mode):\n\n")
            for result in search_user_files("guilds", query):
                f.write(f"{result[0]}\n({result[1]}:{result[2]})\n\n")
    else:
        print("Invalid search mode. Please specify either 'message' or 'user'.")
    
async def get_guild_data(bot, botOwner, discord):
    # Get the bot's guild object by ID
    #print a list of guilds the bot is in
    guildData = []
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            if len(invites) > 0:
                # Return the all in the list of invites
                invite = str(invites)
            else:
                log.warning(f"Failed to get invites for guild with ID {guild.id}")
                await botOwner.send(f"No active invites for guild with ID {guild.id} ({bot.guilds.index(guild)}/{len(bot.guilds)})")
                #invite = None
                # If there are no active invites, create a new one and return it
                # botOwner.send(f"Creating invite for guild with ID {guild.id}")
                # Disabled invite creation because it's sus and takes ages
                # try:
                #     channel = guild.text_channels[0]
                #     invite = await channel.create_invite()
                # except:
                #     # If the bot can't create an invite, return None
                #     print (f"Failed to create invite for guild with ID {guild.id}")
                #     invite = None

        except discord.errors.Forbidden:
            # If the bot doesn't have the permission "Manage Guild" in the guild, it can't get invites
            log.warning(f"Failed to get invites for guild with ID {guild.id}")
            await botOwner.send(f"Failed to get invites for guild with ID {guild.id} ({bot.guilds.index(guild)}/{len(bot.guilds)})")
            invite = None

        # [guildName, guildInvite, guildID, guildOwner, guildMemberCount, guildMemberOnlineCount]
        online_members = len([member for member in guild.members if member.status == discord.Status.online])
        guildData.append([guild.name, invite, guild.id, guild.owner, guild.member_count, online_members])

    return guildData

async def create_guild_invite(bot, botOwner, guildID, discord, expireTime=60):
        # Get the guild object by ID
        try:
            guildID = int(guildID)
        except ValueError:
            log.warning(f"Invalid guild ID: {guildID}")
            await botOwner.send(f"Invalid guild ID: {guildID}")
            return None
        try:
            guild = bot.get_guild((guildID))
        except discord.errors.Forbidden:
            # If the bot failed to get the guild object, it doesn't have access to the guild
            log.warning(f"Failed to get guild with ID {guildID}")
            await botOwner.send(f"Failed to get guild with ID {guildID}")
            return None
        
        # Create an invite for the guild
        try:
            log.info(f"Creating invite for guild with ID {guildID}")
            channel = guild.text_channels[0]
            #invite expires in 1 hour
            invite = await channel.create_invite(max_age=expireTime)
            log.debug(invite)
            invite = str(invite)
        except:
            # If the bot can't create an invite, return None
            log.warning(f"Failed to create invite for guild with ID {guildID}")
            await botOwner.send(f"Failed to create invite for guild with ID {guildID}")
            return None

        return invite


#ENCODING AND DECODING FUNCTIONS
def caesar_cipher_encode(message, key):
    encoded_message = ""
    key = int(key)  # Convert the key to an integer
    for char in message:
        if char.isalpha():
            if char.isupper():
                encoded_char = chr((ord(char) - ord('A') + key) % 26 + ord('A'))
            else:
                encoded_char = chr((ord(char) - ord('a') + key) % 26 + ord('a'))
        else:
            encoded_char = char
        encoded_message += encoded_char
    return encoded_message


def vigenere_cipher_encode(message, key):
    encoded_message = ""
    key_length = len(key)
    key_index = 0
    for char in message:
        if char.isalpha():
            key_char = key[key_index % key_length]
            key_offset = ord(key_char.upper()) - ord('A')
            if char.isupper():
                encoded_char = chr((ord(char) - ord('A') + key_offset) % 26 + ord('A'))
            else:
                encoded_char = chr((ord(char) - ord('a') + key_offset) % 26 + ord('a'))
            key_index += 1
        else:
            encoded_char = char
        encoded_message += encoded_char
    return encoded_message


def atbash_cipher_encode(message):
    encoded_message = ""
    for char in message:
        if char.isalpha():
            if char.isupper():
                encoded_char = chr(ord('Z') - (ord(char) - ord('A')))
            else:
                encoded_char = chr(ord('z') - (ord(char) - ord('a')))
        else:
            encoded_char = char
        encoded_message += encoded_char
    return encoded_message


def caesar_cipher_decode(message, key):
    decoded_message = ""
    key = int(key)  # Convert the key to an integer
    for char in message:
        if char.isalpha():
            if char.isupper():
                decoded_char = chr((ord(char) - ord('A') - key) % 26 + ord('A'))
            else:
                decoded_char = chr((ord(char) - ord('a') - key) % 26 + ord('a'))
        else:
            decoded_char = char
        decoded_message += decoded_char
    return decoded_message


def vigenere_cipher_decode(message, key):
    decoded_message = ""
    key_length = len(key)
    key_index = 0
    for char in message:
        if char.isalpha():
            key_char = key[key_index % key_length]
            key_offset = ord(key_char.upper()) - ord('A')
            if char.isupper():
                decoded_char = chr((ord(char) - ord('A') - key_offset) % 26 + ord('A'))
            else:
                decoded_char = chr((ord(char) - ord('a') - key_offset) % 26 + ord('a'))
            key_index += 1
        else:
            decoded_char = char
        decoded_message += decoded_char
    return decoded_message

def atbash_cipher_decode(message):
    decoded_message = ""
    for char in message:
        if char.isalpha():
            if char.isupper():
                decoded_char = chr(ord('Z') - (ord(char) - ord('A')))
            else:
                decoded_char = chr(ord('z') - (ord(char) - ord('a')))
        else:
            decoded_char = char
        decoded_message += decoded_char
    return decoded_message

def binary_to_text(message):
    # Remove spaces and convert binary string to bytes
    binary_string = ''.join(message.split())
    try:
        byte_data = int(binary_string, 2).to_bytes((len(binary_string) + 7) // 8, 'big')
        return byte_data.decode()
    except ValueError:
        return None

def hex_to_text(message):
    # Remove spaces and convert hex string to bytes
    hex_string = ''.join(message.split())
    try:
        byte_data = bytes.fromhex(hex_string)
        return byte_data.decode()
    except ValueError:
        return None
    
def similar(a, b):
    """Return a similarity score between 0 and 1 for two strings"""
    return SequenceMatcher(None, a, b).ratio()

def convert_str_to_unix_time(string):
    # Parse the string into a time
    try:
        dt = dateutil.parser.parse(string)
    except dateutil.parser._parser.ParserError:
        return None
    # Convert the time object to a Unix timestamp and return it
    return int(time.mktime(dt.timetuple()))

def get_api_ninjas_key():
    with open("config/token.toml") as toml_file:
        data = toml.load(toml_file)
        key = data["api-ninjas-key"]
    return key


def call_api_holidays(country_code, year):
    print ("Switching to API")

    # Look up string to see if it's a holiday
    
    # holiday_type = 'public_holiday'
    api_url = "https://api.api-ninjas.com/v1/holidays?country={}&year={}".format(country_code, year)
    response = requests.get(api_url, headers={'X-Api-Key': get_api_ninjas_key()})
    if response.status_code == requests.codes.ok:
        data = response.json()
    return data

def timecode_convert(time_string, format):
    # Examples:
    # <t:1704206040:R>
    # <t:1704206040:t>
    # <t:1704206040:T>
    # <t:1704206040:d>
    # <t:1704206040:D>
    # <t:1704206040:f>
    # <t:1704206040:F>

    # Convert it to Unix time
    if time_string == None:
        unix_time = time.time()
    else:
        unix_time = convert_str_to_unix_time(time_string)
        if unix_time is None:
            possible_holidays = call_api_holidays("CA", datetime.datetime.now().year)
            possible_holidays.extend(call_api_holidays("CA", datetime.datetime.now().year + 1))
            
            unique_holidays = {}
            today = datetime.datetime.now()

            for holiday in possible_holidays:
                name = holiday["name"].lower()
                date = datetime.datetime.strptime(holiday['date'], "%Y-%m-%d")  # assuming date is in this format

                if name not in unique_holidays:
                    unique_holidays[name] = date
                else:
                    if date > today:
                        if unique_holidays[name] < today or date < unique_holidays[name]:
                            unique_holidays[name] = date
                    # if date is before today, ignore it

            # replace possible_holidays with the unique ones
            possible_holidays = [{'name': name, 'date': date.strftime("%Y-%m-%d")} for name, date in unique_holidays.items()]
                    
            max_similarity = 0
            for holiday in possible_holidays:
                similarity = similar(holiday["name"].lower(), time_string.lower())
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_name = holiday["name"].lower()
                    date = holiday['date']
                    unix_time = convert_str_to_unix_time(date)
            if unix_time is None:
                return None
    format = format.lower()
    if format == "relative":
        return f"<t:{int(unix_time)}:R>\n`<t:{int(unix_time)}:R>`"
    if format == "short time":
        return f"<t:{int(unix_time)}:t>\n`<t:{int(unix_time)}:t>`"
    if format == "long time":
        return f"<t:{int(unix_time)}:T>\n`<t:{int(unix_time)}:T>`"
    if format == "short date":
        return f"<t:{int(unix_time)}:d>\n`<t:{int(unix_time)}:d>`"
    if format == "long date":
        return f"<t:{int(unix_time)}:D>\n`<t:{int(unix_time)}:D>`"
    if format == "long date with short time":
        return f"<t:{int(unix_time)}:f>\n`<t:{int(unix_time)}:f>`"
    if format == "long date with day of the week":
        return f"<t:{int(unix_time)}:F>\n`<t:{int(unix_time)}:F>`"
    else:
        return None

# Other functions
async def log_data_to_csv(bot):
    # Create a csv if one does not exist,
    # otherwise append to the existing csv
    # Format: Time, User Count, Server Count, Total Command Count,

    # Create the csv file if it doesn't exist
    if not os.path.isfile("data/data.csv"):
        #using csv module
        with open("data/data.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "User Count", "Server Count", "Total Command Count"])

    # Get the current time
    time_code = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Get the number of users
    user_count = len(bot.users)
    log.info(f"User count: {user_count}")

    # Get the number of guild
    guild_count = len(bot.guilds)
    log.info(f"Guild count: {guild_count}")

    # Get the total number of commands
    # open data/users.json and get the total number of commands by adding up all the commandsUsed values
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
            total_command_count = 0
            for user_id in users:
                user_data = users[user_id]
                total_command_count += user_data.get("commandsUsed", 0)
    except FileNotFoundError:
        log.error("data/users.json not found")
        total_command_count = 0
    log.info(f"Total command count: {total_command_count}")

    # Write the data to the csv file
    with open("data/data.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([time_code, user_count, guild_count, total_command_count])

def get_date_time_gmt():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def gen_csv_plot(csv_file, draw_user_count, draw_guild_count, draw_command_count, draw_diff_count, time_frame=None):
    with open(csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader, None)  # Skip the header
        data = sorted(reader, key=lambda row: datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"))

        # Determine the time delta based on the time frame
        if time_frame is not None:
            time_delta = datetime.timedelta(days=int(time_frame))
        else:
            time_delta = None 
        # Get the current time
        now = datetime.datetime.now()
        x = []
        y1 = []
        y2 = []
        y3 = []
        y4 = []
        for row in data:
            current_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            # Skip this row if it's not within the time frame
            if time_delta is not None and current_time < now - time_delta:
                print (time_delta)
                print (current_time)
                print (now - time_delta)
                continue
            x.append(current_time)  # Time
            y1.append(int(row[1]))  # User count
            y2.append(int(row[2]))  # Guild count
            if row[3] == "N/A":
                y3.append(0)
            else:
                y3.append(int(row[3]))  # Total command count

            try:
                if row[4] == None:
                    y4.append(0)
                else:
                    y4.append(int(row[4]))
            except IndexError:
                y4.append(0)



        plt.xlabel('Time (s)')
        plt.ylabel('Count')

        if draw_user_count:
            plt.plot(x, y1, label='User count')
        if draw_guild_count:
            plt.plot(x, y2, label='Guild count')
        if draw_command_count:
            plt.plot(x, y3, label='Total command count')
        if draw_diff_count:
            plt.plot(x, y4, label='Command count difference')

        plt.legend()
        plt.xticks(rotation=90)  # Rotate x-axis labels
        plt.tight_layout()  # Adjust layout to ensure labels fit
        plt.savefig(csv_file + '.png')
        plt.close()
        return f"{csv_file}.png"

def qr_code_image_generator(text):
    qr = QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    image_seed = hashlib.md5(text.encode()).hexdigest()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"temp/qr{image_seed}.png")
    return f"temp/qr{image_seed}.png"

def qr_code_text_generator(input=None, invert=False, white='█', black=' ', version=1, border=1, correction='M'):
    """Converts a QR code to ASCII art."""
    # generate/load image
    if input is None or not os.path.isfile(input):
        if input:
            data = input
        else:
            data = input('Enter data to encode: ')

        # parse error correction
        if correction == 'L':
            ecc = constants.ERROR_CORRECT_L
        elif correction == 'Q':
            ecc = constants.ERROR_CORRECT_Q
        elif correction == 'H':
            ecc = constants.ERROR_CORRECT_H
        else: # default M
            ecc = constants.ERROR_CORRECT_M

        qr = QRCode(version=version, box_size=1, border=border, error_correction=ecc)
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color=(0, 0, 0), back_color=(255, 255, 255))
    else:
        try:
            image = Image.open(input)
        except:
            raise ValueError("unable to open file")

    image_array = array(image.getdata())

    width = image.size[0]
    height = image.size[1]

    # get offset
    offset = 0
    while image_array[offset * width + offset][0] == 255:
        offset += 1

    # get scale
    scale = 1
    while image_array[(offset + scale) * width + (offset + scale)][0] == 0:
        scale += 1

    # resize
    image = image.resize((width // scale, height // scale), Image.Resampling.NEAREST)
    image_array = array(image.getdata())
    width = image.size[0]
    height = image.size[1]

    # inverted colors
    if invert:
        image_array = 255 - image_array

    qr_string = ''
    for i in range(0, height, 2):
        for j in range(width):
            if i + 1 < height:
                upper_pixel = image_array[i * width + j][0] < 128
                lower_pixel = image_array[(i + 1) * width + j][0] < 128
                if upper_pixel and lower_pixel:
                    qr_string += white
                elif upper_pixel:
                    qr_string += '▀'
                elif lower_pixel:
                    qr_string += '▄'
                else:
                    qr_string += black
            else:
                if image_array[i * width + j][0] < 128:
                    qr_string += '▀'
                else:
                    qr_string += black
        qr_string += '\n'
    # remove first space from each line
    if qr_string.startswith(' '):
        qr_string = qr_string[1:]
        qr_string = '\n' + qr_string
    qr_string = qr_string.replace(' \n', '\n')
    qr_string = qr_string.replace('\n ', '\n')
    return qr_string

async def ai_image_gen(prompt, enhancer):
    # read wordblacklist.json
    async with aiofiles.open("config/wordblacklist.json", "r") as f:
        banned_words = await f.read()
        banned_words = json.loads(banned_words)["words"]
    for word in banned_words:
        if word in prompt.lower():
            return None
        
    enhancer_prompts = {
    "none": f"{prompt}",

    "digital painting": f"{prompt}, glow effects, godrays, Hand drawn, render, 8k, octane render, cinema 4d, blender, dark, atmospheric 4k ultra detailed, cinematic, Sharp focus, big depth of field, Masterpiece, colors, 3d octane render, 4k, concept art, trending on artstation, hyperrealistic, Vivid colors, extremely detailed CG unity 8k wallpaper, trending on CGSociety, Intricate, High Detail, dramatic",
    
    "indie game": f"{prompt}, Indie game art, Vector Art, Borderlands style, Arcane style, Cartoon style, Line art, Disctinct features, Hand drawn, Technical illustration, Graphic design, Vector graphics, High contrast, Precision artwork, Linear compositions, Scalable artwork, Digital art, cinematic sensual, Sharp focus, humorous illustration, big depth of field, Masterpiece, trending on artstation, Vivid colors, trending on ArtStation, trending on CGSociety, Intricate, Low Detail, dramatic",
    
    "photo": f"{prompt}, Photorealistic, Hyperrealistic, Hyperdetailed, analog style, soft lighting, subsurface scattering, realistic, heavy shadow, masterpiece, best quality, ultra realistic, 8k, golden ratio, Intricate, High Detail, film photography, soft focus",
    
    "film noir": f"{prompt}, (b&w, Monochromatic, Film Photography:1.3),  Photorealistic, Hyperrealistic, Hyperdetailed, film noir, analog style, soft lighting, subsurface scattering, realistic, heavy shadow, masterpiece, best quality, ultra realistic, 8k, golden ratio, Intricate, High Detail, film photography, soft focus",
    
    "isometric room": f"{prompt}, Tiny cute isometric in a cutaway box, soft smooth lighting, soft colors, 100mm lens, 3d blender render",
    
    "space hologram": f"{prompt}, hologram floating in space, a vibrant digital illustration, dribbble, quantum wavetracing, black background, behance hd",
    
    "cute creature": f"{prompt}, 3d fluffy, closeup cute and adorable, cute big circular reflective eyes, long fuzzy fur, Pixar render, unreal engine cinematic smooth, intricate detail, cinematic",
    
    "realistic portrait": f"{prompt}, RAW candid cinema, 16mm, color graded portra 400 film, remarkable color, ultra realistic, textured skin, remarkable detailed pupils, realistic dull skin noise, visible skin detail, skin fuzz, dry skin, shot with cinematic camera",
    
    "realistic landscape": f"long shot scenic professional photograph of {prompt}, perfect viewpoint, highly detailed, wide-angle lens, hyper realistic, with dramatic sky, polarizing filter, natural lighting, vivid colors, everything in sharp focus, HDR, UHD, 64K",
}

    prompt = enhancer_prompts.get(enhancer.lower(), prompt)
    
    # Initialize the Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://sdxlturbo.ai/")
        await page.fill('input[name="prompt"]', prompt, timeout=15000)
        # Wait until the image has loaded
        await page.wait_for_selector('//img[@alt="Generated"]')
        image_url = await page.get_attribute('//img[@alt="Generated"]', "src")
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    seed = hashlib.md5(prompt.encode()).hexdigest()
                    async with aiofiles.open(f"temp/sdturbo{seed}.jpg", 'wb') as f:
                        await f.write(await resp.read())
        # Close the browser
        await browser.close()
    return f"temp/sdturbo{seed}.jpg"

