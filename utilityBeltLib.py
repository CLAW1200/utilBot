import os
import random
import logging as log
import time
import discord
import toml
from PIL import Image, ImageSequence, ImageFont, ImageDraw
import requests
import ffmpeg
import json
import datetime
import urllib
import shutil
import app

def restart_script():
    app.main()

def update_bot():
    """
    Update the bot and restart it
    """        
    # Pull the latest commit
    os.system("git pull")

    # Restart the bot
    restart_script()


def is_bot_version_latest():
    """
    Check for an update to the bot via github
    """
    # Get the current commit hash
    current_commit_hash = get_current_commit_hash()

    # Get the latest commit hash from github
    latest_commit_hash = get_latest_commit_hash()

    # Check if the bot is up to date
    if current_commit_hash == latest_commit_hash:
        return True
    else:
        return False
    
def get_current_commit_hash():
    """
    Get the current commit hash of the bot
    """
    # Get the current commit hash
    with open(".git/refs/heads/master", "r") as f:
        current_commit_hash = f.read().strip()
    print (f"Current commit hash: {current_commit_hash}")
    return current_commit_hash

def get_latest_commit_hash():
    """
    Use git command line to get the latest commit hash from github
    """
    # get latest commit hash from github
    os.system("git fetch")
    os.system("git reset --hard origin/master")
    with open(".git/refs/heads/master", "r") as f:
        latest_commit_hash = f.read().strip().strip("'")
    print (f"Latest commit hash: {latest_commit_hash}")




MESSAGE = 25
DIRECT_MESSAGE = 30
COMMAND = 35
remove_char = "'"

# Define custom log level names
log.addLevelName(MESSAGE, "MESSAGE")
log.addLevelName(DIRECT_MESSAGE, "DIRECT_MESSAGE")
log.addLevelName(COMMAND, "COMMAND")

# Configure the logger
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode="a", filename="app.log")

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

def logging_direct_message(message):
    log.log(DIRECT_MESSAGE, f"DIRECT MESSAGE FROM: '{str(message.author.name).strip(remove_char)}#{message.author.discriminator}'\n    -> {message.content}\n        -> {message.attachments} {message.embeds}")

def logging_command(ctx, *args):
    if ctx.guild == None:
        logging_command_direct_message(ctx, *args)
        return

    print (        f"SERVER: '{str(ctx.guild.name).strip(remove_char)}' ({ctx.guild.id}) IN CHANNEL: '{str(ctx.channel.name).strip(remove_char)}' ({ctx.channel.id})\n    -> '{str(ctx.author.name).strip(remove_char)}#{ctx.author.discriminator}' RAN COMMAND: '{ctx.command}'\n        -> {args}")
    log.log(
        COMMAND,
        f"SERVER: '{str(ctx.guild.name).strip(remove_char)}' ({ctx.guild.id}) IN CHANNEL: '{str(ctx.channel.name).strip(remove_char)}' ({ctx.channel.id})\n    -> '{str(ctx.author.name).strip(remove_char)}#{ctx.author.discriminator}' RAN COMMAND: '{ctx.command}'\n        -> {args}"
    )

def logging_command_direct_message(ctx, *args):
    print (        f"DIRECT MESSAGE FROM: '{str(ctx.author.name).strip(remove_char)}#{ctx.author.discriminator}'\n    -> RAN COMMAND: '{ctx.command}'\n        -> {args}")
    log.log(
        COMMAND,
        f"DIRECT MESSAGE FROM: '{str(ctx.author.name).strip(remove_char)}#{ctx.author.discriminator}'\n    -> RAN COMMAND: '{ctx.command}'\n        -> {args}"
    )


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
    log.debug(f"Archiving file '{time.gmtime}{file}'")
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
        if os.path.getmtime(f"temp/{file}") < time.time() - (5 * 60):
            try:
                os.remove(f"temp/{file}")
                log.debug(f"Removed old file '{file}'")
            except Exception as e:
                log.error(f"Error removing old file '{file}': {e}")

def convert_image_to_gif(image_link):
    clean_up_temp_files()
    #this function will take a link to an image and convert it to a gif
    #download image in temp folder
    image_seed = random.randint(10000,99999)
    output_path = f"temp/image{image_seed}.gif"
    #download image
    with open(f"temp/image{image_seed}.png", "wb") as f:
        f.write(requests.get(image_link).content)
    
    # Open the PNG image
    image = Image.open(f"temp/image{image_seed}.png")

    # Convert the image to GIF
    image.save(output_path, format="GIF", save_all=True)
    image.close()
    os.remove(f"temp/image{image_seed}.png")
    log.debug(f"Converted image '{image_link}' to gif '{output_path}'")
    return output_path

def convert_video_to_gif(video_link, fps=25, scale = None):
    clean_up_temp_files()
    #this function will take a link to an image and convert it to a gif
    #download image in temp folder
    fileType = urllib.parse.urlparse(video_link).path.split(".")[-1]
    video_seed = random.randint(10000,99999)
    output_path = f"temp/video{video_seed}.gif"
    #download image
    with open(f"temp/video{video_seed}.{fileType}", "wb") as f:
        f.write(requests.get(video_link).content)
    print (fps)
    print (scale)
    # Open the Video file and convert to gif in good quality
    try:
        video = ffmpeg.input(f"temp/video{video_seed}.{fileType}")
        if scale != None:
            video = ffmpeg.filter(video, 'scale', scale)
        video = ffmpeg.output(video, output_path, r=fps, pix_fmt='rgb24')
        ffmpeg.run(video)
        os.remove(f"temp/video{video_seed}.{fileType}")
        log.debug(f"Converted video '{video_link}' to gif '{output_path}'")
        return output_path
    except Exception as e:
        log.error(f"Error converting video '{video_link}' to gif: {e}")
        return None


def get_file_size(link):
    #function to check the size of a video or image link
    response = requests.get(link, stream=True)
    if 'Content-Length' in response.headers:
        file_size = int(response.headers['Content-Length']) 
        return file_size
    else:
        return None

def add_speech_bubble(image_link, speech_bubble_y_scale=0.2):
    clean_up_temp_files()
    """
    Add a speech bubble to the top of the image or each frame of a GIF.
    """
    speechBubble = Image.open("assets/speechBubble.png").convert("RGBA")
    image_seed = random.randint(10000, 99999)
    output_path = f"temp/image{image_seed}"

    # Download the image
    with open(f"{output_path}.temp", "wb") as f:
        f.write(requests.get(image_link).content)
    image = Image.open(f"{output_path}.temp")
    # Check if the image is a GIF
    is_gif = image.format == 'GIF'

    if is_gif:
        frames = []
        for frame in ImageSequence.Iterator(image):
            frame = frame.convert("RGBA")
            bubble_height = int(frame.size[1] * speech_bubble_y_scale)  # Calculate bubble height as 20% of the image height
            speechBubble_resized = speechBubble.resize((frame.size[0], bubble_height))
            frame.paste(speechBubble_resized, (0, 0), speechBubble_resized)
            frames.append(frame)

        output_path = f"{output_path}.gif"
        frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0)

    else:
        image = image.convert("RGBA")
        bubble_height = int(image.size[1] * speech_bubble_y_scale)  # Calculate bubble height as 20% of the image height
        speechBubble_resized = speechBubble.resize((image.size[0], bubble_height))
        image.paste(speechBubble_resized, (0, 0), speechBubble_resized)

        # Save the image as a PNG
        output_path = f"{output_path}.png"
        image.save(output_path)

    image.close()
    speechBubble.close()
    return output_path

def add_impact_font(image_link, top_text, bottom_text, font_size, font_color=(255, 255, 255), font_outline_color=(0, 0, 0)):
    # Create a temporary directory if it doesn't exist
    temp_dir = './temp/'
    clean_up_temp_files()

    random_seed = random.randint(10000, 99999)

    font_outline_width = font_size // 25

    # Download the image or GIF from the link
    response = requests.get(image_link)
    if response.status_code == 200:
        temp_file_path = os.path.join(temp_dir, f'temp_image{random_seed}')
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
    else:
        print('Failed to download the image or GIF.')
        return

    # Open the image or GIF using Pillow
    image = Image.open(temp_file_path)

    # Check if the image is a GIF
    is_gif = image.format == 'GIF'

    # Load the Impact font
    font_path = f'assets/impact.ttf'
    font = ImageFont.truetype(font_path, font_size)

    # Create a draw object
    draw = ImageDraw.Draw(image)

    # Calculate the text dimensions
    top_text_width, top_text_height = draw.textsize(top_text, font=font)
    bottom_text_width, bottom_text_height = draw.textsize(bottom_text, font=font)

    # Calculate the position for the top and bottom text
    image_width, image_height = image.size
    top_text_x = (image_width - top_text_width) // 2
    top_text_y = 0
    bottom_text_x = (image_width - bottom_text_width) // 2
    bottom_text_y = image_height - bottom_text_height

    if is_gif:
        # Get the original duration of the GIF
        original_duration = image.info.get('duration', 100)

        # Iterate over each frame of the GIF and add the text
        frames = []
        for frame in range(0, image.n_frames):
            image.seek(frame)
            frame_image = image.copy()

            draw = ImageDraw.Draw(frame_image)
            
            draw.text((top_text_x, top_text_y), top_text, font=font, fill=font_color, stroke_width=font_outline_width,
                      stroke_fill=font_outline_color)
            draw.text((bottom_text_x, bottom_text_y), bottom_text, font=font, fill=font_color, stroke_width=font_outline_width,
                      stroke_fill=font_outline_color)

            frames.append(frame_image)

        # Save the frames as an animated GIF with original duration
        output_file_path = os.path.join(temp_dir, f'output{random_seed}.gif')
        frames[0].save(output_file_path, save_all=True, append_images=frames[1:], optimize=False, duration=original_duration, loop=0)

    else:
        
        draw.text((top_text_x, top_text_y), top_text, font=font, fill=font_color, stroke_width=font_outline_width,
                          stroke_fill=font_outline_color)
        draw.text((bottom_text_x, bottom_text_y), bottom_text, font=font, fill=font_color, stroke_width=font_outline_width,
                          stroke_fill=font_outline_color)
        
        # Save the image as a PNG
        output_file_path = os.path.join(temp_dir, f'output{random_seed}.png')
        image.save(output_file_path, 'PNG')

    # Return the output file path
    return output_file_path

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
    

async def get_guild_invite(bot):
    # Get the bot's guild object by ID
    #print a list of guilds the bot is in
    guildData = []
    for guild in bot.guilds:
       
        # Check if there are any active invites for the guild
        try:
            invites = await guild.invites()
            if len(invites) > 0:
                # Return the first invite in the list of invites
                invite = str(invites[0])
            else:
                #invite = None
                # If there are no active invites, create a new one and return it
                try:
                    channel = guild.text_channels[0]
                    invite = await channel.create_invite()
                except:
                    # If the bot can't create an invite, return None
                    print (f"Failed to create invite for guild with ID {guild.id}")
                    invite = None

        except discord.errors.Forbidden:
            # If the bot doesn't have the permission "Manage Guild" in the guild, it can't get invites
            print (f"Failed to get invites for guild with ID {guild.id}")
            invite = None

        # [guildName, guildInvite, guildID, guildOwner, guildMemberCount, guildMemberOnlineCount]
        online_members = len([member for member in guild.members if member.status == discord.Status.online])
        guildData.append([guild.name, invite, guild.id, guild.owner, guild.member_count, online_members])

    return guildData


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