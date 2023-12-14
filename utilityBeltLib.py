import os
import random
import logging
import time
import discord
import toml
from PIL import Image
import requests
import json
import datetime
import urllib
import shutil
import subprocess
import hashlib
import csv
remove_char = "'"

# Configure the logger

# Create a log
log = logging.getLogger('Utility Belt Lib')
log.setLevel(logging.DEBUG)

# Create a formatter and set it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('app.log')
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


def edit_user_data(user, field, data):
    # Edit users.json, add data to key
    user_id = str(user.id)
    try:
        with open("users.json", "r+") as f:
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
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

def add_user_data(user, field, data):
    # Edit users.json, add data to key if it doesn't exist
    user_id = str(user.id)
    try:
        with open("users.json", "r+") as f:
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
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

def get_user_data(user, field):
    # Get data from users.json
    user_id = str(user.id)
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
            if user_id in users:
                user_data = users[user_id]
                return user_data.get(field, 0)
            else:
                return 0
    except FileNotFoundError:
        return 0
    
def archive_file(file):
    #move file to /archive/
    log.info(f"Archiving file '{time.gmtime}{file}'")
    try:
        os.rename(file, f"archive/{file}")
    except Exception as e:
        log.error(f"Error archiving file '{file}': {e}")

def zip_archive_folder(folder):
    shutil.make_archive('guilds', 'zip', 'guilds')
    return f"{folder}.zip"
   
def read_log():
    log.debug("Reading log")
    with open("app.log", "r") as f:
        return f.read()
    
def clear_log():
    open("app.log", "w").close()
    log.debug("Log cleared")

def read_toml_var(var):
    log.debug(f"Reading variable '{var}' from config")
    configFile = "config.toml"
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

def convert_image_to_gif(image_link):
    clean_up_temp_files()
    # this function will take a link to an image and convert it to a gif by simply changing the extension
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
    clean_up_temp_files()
    #this function will take a link to an video and convert it to a gif
    #download video in temp folder
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
        subprocess.call(['ffmpeg', '-i', f"temp/{video_seed}", '-filter_complex', f'[0:v] fps=fps={fps},{scale},split [a][b];[a] palettegen [p];[b][p] paletteuse', output_path])
        os.remove(f"temp/{video_seed}")
        log.info(f"Converted video '{video_link}' to gif '{output_path}'")
        return output_path
    except Exception as e:
        log.error(f"Error converting video '{video_link}' to gif: {e}")
        return None


def get_file_size(link):
    # function to check the size of a video or image link
    try:
        response = requests.get(link, stream=True)
        download_start = response.raw.tell()
        response.raw.read(1024)  # read only 1024 bytes
        download_end = response.raw.tell()
        estimated_size = download_end - download_start
        return estimated_size * 1024  # estimate for the whole file
    except Exception as e:
        log.error(f"Error getting file size for '{link}': {e}")
        return None
    
def add_speech_bubble(image_link, speech_bubble_y_scale=0.2):
    clean_up_temp_files()
    """
    Add a speech bubble to the top of the image or each frame of a GIF.
    """
    from PIL import Image
    data = requests.get(image_link).content
    speechBubble = "assets/speechBubble.png"
    image_seed = hashlib.md5(requests.get(image_link).content).hexdigest()
    output_path = f"temp/{image_seed}.gif"
    # save the image to a file
    with open(output_path, 'wb') as f:
        f.write(data)
    # Load both images
    image = Image.open(output_path).convert("RGBA")
    bubble = Image.open(speechBubble).convert("RGBA")

    # Calculate 20% of the height of the first image
    new_height = int(image.height * 0.2)

    # Resize the speech bubble to exactly 20% of the image's height and 100% of the image's width
    bubble = bubble.resize((image.width, new_height))

    # Create a new image with the same size as the original image
    result = Image.new("RGBA", image.size)

    # Paste the resized speech bubble onto the new image at the top left corner (0,0)
    result.paste(bubble, (0,0), bubble)

    # Iterate over each pixel in the images
    for x in range(image.width):
        for y in range(image.height):
            # Get the current pixel
            pixel_image = image.getpixel((x, y))
            pixel_result = result.getpixel((x, y))

            # If the pixel in the result image is not completely transparent
            if pixel_result[3] > 0:  # Alpha value is not 0
                # Make the corresponding pixel in the first image completely transparent
                result.putpixel((x, y), (pixel_image[0], pixel_image[1], pixel_image[2], 0))
            else:
                # Otherwise, keep the original pixel
                result.putpixel((x, y), pixel_image)

    # Save the result
    result.save(output_path, "GIF")
    log.info(f"Added speech bubble to image '{image_link}'")
    return output_path


def gif_search(query):
    tokenFile = "token.toml"
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
    configFile = "config.toml"
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
    
async def get_guild_invite(bot, botOwner):
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

async def create_guild_invite(bot, botOwner, guildID, expireTime=60):
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
    

# Other functions
    
async def log_data_to_csv(bot):
    # Create a csv if one does not exist,
    # otherwise append to the existing csv
    # Format: Time, User Count, Server Count, Total Command Count,

    # Create the csv file if it doesn't exist
    if not os.path.isfile("data.csv"):
        #using csv module
        with open("data.csv", "w") as f:
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
    total_command_count = "N/A"

    # Write the data to the csv file
    with open("data.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([time_code, user_count, guild_count, total_command_count])

def get_date_time_gmt():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")