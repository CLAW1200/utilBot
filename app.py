import os
import random
import logging as log
import time
import discord
import toml
import asyncio
from PIL import Image, ImageSequence, ImageFont, ImageDraw
import requests
import ffmpeg
import urllib.parse
import aiohttp
from pint import UnitRegistry
import json
ureg = UnitRegistry()

MESSAGE = 25
DIRECT_MESSAGE = 30
COMMAND = 35

remove_char = "'"

keywords = {
    "https://discord",
    "claw",
}

# Define custom log level names
log.addLevelName(MESSAGE, "MESSAGE")
log.addLevelName(DIRECT_MESSAGE, "DIRECT_MESSAGE")
log.addLevelName(COMMAND, "COMMAND")

# Configure the logger
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode="a", filename="app.log")

# Create custom log functions
def logging_message(message):
    log.log(MESSAGE, f"SERVER: '{str(message.guild.name).strip(remove_char)}' ({message.guild.id}) IN CHANNEL: '{str(message.channel.name).strip(remove_char)}' ({message.channel.id})\n    -> '{str(message.author.name).strip(remove_char)}#{message.author.discriminator}' SAID: {message.content}\n        -> {message.attachments} {message.embeds}")

def logging_direct_message(message):
    log.log(DIRECT_MESSAGE, f"DIRECT MESSAGE FROM: '{str(message.author.name).strip(remove_char)}#{message.author.discriminator}'\n    -> {message.content}\n        -> {message.attachments} {message.embeds}")

def logging_command(ctx, *args):
    log.log(
        COMMAND,
        f"SERVER: '{str(ctx.guild.name).strip(remove_char)}' ({ctx.guild.id}) IN CHANNEL: '{str(ctx.channel.name).strip(remove_char)}' ({ctx.channel.id})\n    -> '{str(ctx.author.name).strip(remove_char)}#{ctx.author.discriminator}' RAN COMMAND: '{ctx.command}'\n        -> {args}"
    )

tokenFile = "token.toml"
with open(tokenFile) as toml_file:
    data = toml.load(toml_file)
    TOKEN = data["token"]
    TOP_GG_TOKEN = data["top-gg-token"]
    log.debug(f"Token read from '{tokenFile}'")

#if there is no temp folder make one
if not os.path.exists("temp"):
    os.makedirs("temp")

def edit_user_data(user, field, data):
    # Edit users.json, add data to key
    with open("users.json", "r") as f:
        users = json.load(f)
    
    user_id = str(user.id)
    if user_id in users:
        user_data = users[user_id]
        user_data[field] = data
    else:
        user_data = {field: data}

    users[user_id] = user_data
    
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def get_user_data(user, field):
    #get data from users.json
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
        return users[str(user.id)][field]
    except KeyError:
        return 0
    

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

def is_admin(user):
    log.debug(f"Checking if user '{user.name}#{user.discriminator}' is an admin")
    if f"{user.name}#{user.discriminator}" in read_toml_var("admins"):
        log.debug(f"User '{user.name}#{user.discriminator}' is an admin")
        return True

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

def convert_video_to_gif(video_link, fps = 20, scale = None):
    clean_up_temp_files()
    #this function will take a link to an image and convert it to a gif
    #download image in temp folder
    fileType = video_link.split(".")[-1]
    video_seed = random.randint(10000,99999)
    output_path = f"temp/video{video_seed}.gif"
    #download image
    with open(f"temp/video{video_seed}.{fileType}", "wb") as f:
        f.write(requests.get(video_link).content)
    
    # Open the PNG image
    video = ffmpeg.input(f"temp/video{video_seed}.{fileType}")
    video = ffmpeg.filter(video, 'fps', fps=fps, round='up')
    if scale != None:
        video = ffmpeg.filter(video, 'scale', scale, -1)
    video = ffmpeg.output(video, output_path)
    ffmpeg.run(video)
    os.remove(f"temp/video{video_seed}.{fileType}")
    log.debug(f"Converted video '{video_link}' to gif '{output_path}'")
    return output_path

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

async def get_guild_invite(bot):
    # Get the bot's guild object by ID
    #print a list of guilds the bot is in
    guildNameResults = []
    guildInviteResults = []
    guildInfo = []
    for guild in bot.guilds:

        if guild is None:
            print (f"Failed to get guild with ID {guild.id}")
            pass

        guildInfo.append(f"Guild ID: {guild.id}\nGuild Owner: {guild.owner}\nGuild Member Count: {guild.member_count}\nGuild Members Online Count: {sum(member.status != discord.Status.offline for member in guild.members)}")
        guildNameResults.append(str(guild.name))
        
        # Check if there are any active invites for the guild
        try:
            invites = await guild.invites()
            if len(invites) > 0:
                # Return the first invite in the list of invites
                guildInviteResults.append(str(invites[0]))

        except discord.Forbidden:
            # If the bot doesn't have the permission "Manage Guild" in the guild, it can't get invites
            print (f"Failed to get invites for guild with ID {guild.id}")
            guildInviteResults.append("No Invite")
            continue
        try:
            # Create a new invite and return it
            channel = guild.text_channels[0]
            invite = await channel.create_invite()
            guildInviteResults.append(str(invite))
        except:
            # If the bot can't create an invite, return None
            print (f"Failed to create invite for guild with ID {guild.id}")
            guildInviteResults.append("Invite Creation Failed")
            continue

    return guildNameResults, guildInviteResults, guildInfo


def main():
    log.debug("Starting Main()")
    bot = discord.Bot(intents=discord.Intents.all())
    log.debug("Bot object created")

    def check_bot_permissions(ctx):
        binary_guild_permissions = bin(ctx.guild.me.guild_permissions.value)
        binary_required_permissions = bin(read_toml_var("permissionsInt"))

        #perform binary AND operation on the two binary strings
        check = int(binary_guild_permissions, 2) & int(binary_required_permissions, 2)
        if check == int(binary_required_permissions, 2):
            return True
        else:
            return False
    
    async def command_topper(ctx):
        edit_user_data(ctx.author, "commandsUsed", get_user_data(ctx.author, "commandsUsed") + 1)
        if get_user_data(ctx.author, "commandsUsed") <= 1:
            await ctx.respond(f"Welcome to Utility Belt! You can use **/help** to get a list of commands.\nRemember to use **/vote** if you find me useful (This will be the only reminder)", ephemeral=True)

        if not check_bot_permissions(ctx):
            await ctx.respond("Warning: I am missing some permissions which may cause errors. Please use /update-permissions to avoid any problems using commands", ephemeral=True)
            return False
        return True

    @bot.slash_command(name="log", description="Get the log file")
    async def send_log_command(
        ctx: discord.ApplicationContext,
        clearLog: discord.Option(bool, name="clear-log", description="Clear the log file after sending it?"),
    ):
        if is_admin(ctx.author):
            await ctx.user.send(file=discord.File("app.log"))
            await ctx.respond("Sent log file.", ephemeral=True)
            if clearLog == True:
                clear_log()
        else:
            await ctx.respond(f"That command is offline right now.", ephemeral=True)
        logging_command(ctx, clearLog)

    @bot.slash_command(name="image-to-gif", description="Take an image link and send it as a gif")
    async def image_to_gif_command(ctx: discord.ApplicationContext, image_link: str):
        if get_file_size(image_link) > read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        await ctx.respond(f"Converting image to gif... ") # this message will be deleted when the gif is sent
        try:
            newGif = convert_image_to_gif(image_link)
            await ctx.edit(content = f"Here is your gif!" , file=discord.File(newGif))
            os.remove(newGif)
            log.info(f"Converted image {image_link}")
        except Image.UnidentifiedImageError:
            await ctx.edit(content = f"Sorry, but that image link is invalid!")
        await command_topper(ctx)
        logging_command(ctx, image_link)

    @bot.slash_command(name="video-to-gif", description="Take a video link and send it as a gif")
    async def video_to_gif_command(
        ctx: discord.ApplicationContext,
        video_link: str,
        fps: discord.Option(int, "The FPS of the gif", required=False, default=20),
        scale: discord.Option(int, "The scale of the gif", required=False, default=320),
    ):
        #do not download videos larger than maxFileSize
        if get_file_size(video_link) > read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        
        if fps > 25:
            await ctx.respond(f"Sorry, but the max FPS is 25!", ephemeral=True)
            return
        
        if scale > 500:
            await ctx.respond(f"Sorry, but the max scale is 500px!", ephemeral=True)
            return
        
        await ctx.respond(f"Converting video to gif... ")
        try:
            newGif = convert_video_to_gif(video_link, fps, scale)
            await ctx.edit(content = f"Here is your gif!" , file=discord.File(newGif))
            os.remove(newGif)
            log.info(f"Converted image {video_link}")
        except Exception as e:
            await ctx.edit(content = f"Sorry, but that video link is invalid!")
        await command_topper(ctx)
        logging_command(ctx, video_link, fps, scale)

    @bot.slash_command(name="speech-bubble", description="Add a speech bubble to an image")
    async def speech_bubble_command(
        ctx: discord.ApplicationContext,
        image_link: str,
        speech_bubble_size: discord.Option(float, "The size of the speech bubble in the y axis", required=False, default=0.2),
    ):
        #do not download videos larger than maxFileSize
        if get_file_size(image_link) > read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        
        if speech_bubble_size > 1 or speech_bubble_size < 0:
            await ctx.respond(f"Sorry, values between 0 and 1 only!", ephemeral=True)
            return
        await ctx.respond(f"Adding speech bubble to image... ")
        try:
            newImage = add_speech_bubble(image_link, speech_bubble_size)
            await ctx.edit(content = (f"Here is your image!") , file=discord.File(newImage))
            os.remove(newImage)
            logging_command(f"Added speech bubble to image {image_link}")
        except Exception as e:
            await ctx.edit(content = f"Sorry, but that image link is invalid!")
            print (e)
            log.error(e)
        await command_topper(ctx)
        logging_command(ctx, image_link, speech_bubble_size)

    @bot.slash_command(name="update-permissions", description="Update the bot's permissions")
    async def update_permissions(ctx):
        if ctx.guild == None:
            await ctx.respond(f"Sorry, but this command can only be used in a server!", ephemeral=True)
            return
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        
        if check_bot_permissions(ctx):
            await ctx.respond(f"Permissions are already up to date!", ephemeral=True)
            return
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={read_toml_var('permissionsInt')}"
        await ctx.respond(f"{inviteLink}", ephemeral=True)
        logging_command(ctx)

    @bot.slash_command(name="impact", description="Add impact font to an image")
    async def impact_command(
        ctx: discord.ApplicationContext,
        
        image_link: str,
        top_text: discord.Option(str, "The top text", required=False, default=""),
        bottom_text: discord.Option(str, "The bottom text", required=False, default=""),
        font_size: discord.Option(int, "The font size", required=False, default=50),
        font_color: discord.Option(str, "The font color", required=False, default="white"),  
    ):
        await ctx.respond(f"Adding impact font to image... ")

        newImage = add_impact_font(image_link, top_text, bottom_text, font_size, font_color)
        await ctx.edit(content = (f"Here is your image!") , file=discord.File(newImage))
        os.remove(newImage)
        log.info(f"Added impact font to image {image_link}")
        await command_topper(ctx)
        logging_command(ctx, image_link, top_text, bottom_text, font_size, font_color)

    @bot.slash_command(name="invite", description="Get the bot's invite link")
    async def invite_command(ctx):
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={read_toml_var('permissionsInt')}"
        await ctx.respond(f"{inviteLink}", ephemeral=True)
        await command_topper(ctx)
        logging_command(ctx)

    @bot.slash_command(name="urban", description="Find a definition of a word on urban dictionary")
    async def urban_command(
        ctx: discord.ApplicationContext,
        word: str,
        random_result: discord.Option(bool, "Whether to get a random result", required=False, default=False),
    ):
        """Fetches the definition of a word from Urban Dictionary."""
        async with aiohttp.ClientSession() as session:
            word_encoded = urllib.parse.quote_plus(word)
            url = f'https://api.urbandictionary.com/v0/define?term={word_encoded}'
            async with session.get(url) as resp:
                data = await resp.json()
                
                if len(data['list']) == 0:
                    await ctx.send("No definition found.")
                    return
                
                if random_result:
                    data['list'] = [random.choice(data['list'])]

                #make sure the definition isn't longer than 1024 characters
                if len(data['list'][0]['definition']) > 1024:
                    data['list'][0]['definition'] = data['list'][0]['definition'][:1021] + "..."
                if len(data['list'][0]['example']) > 1024:
                    data['list'][0]['example'] = data['list'][0]['example'][:1021] + "..."

                definition = data['list'][0]['definition']
                example = data['list'][0]['example']
                
                embed = discord.Embed(title=f"Definition of {word}", color=discord.Color.blue())
                embed.add_field(name="Definition", value=definition, inline=False)
                embed.add_field(name="Example", value=example, inline=False)
                await ctx.respond(embed=embed)
        await command_topper(ctx)
        logging_command(ctx, word, random_result)

    @bot.slash_command(name="urban-random-word", description="Get a random word from urban dictionary")
    async def random_word_command(ctx):
        """Gets a random word from Urban Dictionary."""
        async with aiohttp.ClientSession() as session:
            url = 'https://api.urbandictionary.com/v0/random'
            async with session.get(url) as resp:
                data = await resp.json()
                
                word = data['list'][0]['word']
                definition = data['list'][0]['definition']
                example = data['list'][0]['example']
                
                embed = discord.Embed(title=f"Random Word: {word}", color=discord.Color.green())
                embed.add_field(name="Definition", value=definition, inline=False)
                embed.add_field(name="Example", value=example, inline=False)
                await ctx.respond(embed=embed)
        await command_topper(ctx)
        logging_command(ctx, word)

    @bot.slash_command(name="units", description="Convert units")
    async def convert(ctx, value: float, unit_from: str, unit_to: str):
        try:
            # Parse the units
            unit_from = ureg(unit_from)
            unit_to = ureg(unit_to)

            # Perform the conversion
            converted_value = value * unit_from.to(unit_to)
            unit_from = str(unit_from).split(" ")[1]
            unit_to = str(unit_to).split(" ")[1]

            embed = discord.Embed(title=f"Units Conversion", color=discord.Color.green())
            embed.add_field(name="Value", value=value, inline=False)
            embed.add_field(name="Unit From", value=unit_from, inline=False)
            embed.add_field(name="Unit To", value=unit_to, inline=False)
            embed.add_field(name="Converted Value", value=converted_value, inline=False)
            await ctx.respond(embed=embed)

        except Exception as e:
            await ctx.respond(f"{str(e)}")
        await command_topper(ctx)
        logging_command(ctx, value, unit_from, unit_to)

    @bot.slash_command(name="new-note", description="Write a new note")
    async def new_note_command(ctx, note: str):
        """Create a new note for the user"""
        notes = {}

        try:
            with open("notes.json", "r") as f:
                notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        user_notes = notes.get(str(ctx.author.id), [])
        user_notes.append(note)
        notes[str(ctx.author.id)] = user_notes

        with open("notes.json", "w") as f:
            json.dump(notes, f, indent=4)

        await ctx.respond("New note added!", ephemeral=True)
        await command_topper(ctx)
        logging_command(ctx, note)

    @bot.slash_command(name="edit-note", description="Edit a note")
    async def edit_note_command(ctx, index: int, note: str):
        """Edit an existing note for the user"""
        notes = {}

        try:
            with open("notes.json", "r") as f:
                notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        user_notes = notes.get(str(ctx.author.id), [])

        if 1 <= index <= len(user_notes):
            user_notes[index - 1] = note
            notes[str(ctx.author.id)] = user_notes

            with open("notes.json", "w") as f:
                json.dump(notes, f, indent=4)

            await ctx.respond(f"Note {index} updated!", ephemeral=True)
        else:
            await ctx.respond("Invalid note index!", ephemeral=True)
        await command_topper(ctx)
        logging_command(ctx, index, note)


    @bot.slash_command(name="my-notes", description="Read your notes")
    async def my_notes_command(ctx):
        """Read the user's notes"""
        notes = {}

        try:
            with open("notes.json", "r") as f:
                notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        user_notes = notes.get(str(ctx.author.id), [])

        if user_notes:
            formatted_notes = '\n'.join(f"{i+1}. {note}" for i, note in enumerate(user_notes))
            await ctx.respond(f"Your notes:\n{formatted_notes}", ephemeral=True)
        else:
            await ctx.respond("You have no notes!", ephemeral=True)
        await command_topper(ctx)
        logging_command(ctx)

    @bot.slash_command(name="delete-note", description="Delete a note")
    #delete all or delete one
    async def delete_note_command(ctx, index: int = None):
        """Delete a note for the user"""
        notes = {}

        try:
            with open("notes.json", "r") as f:
                notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        user_notes = notes.get(str(ctx.author.id), [])

        if user_notes:
            if index is None:
                notes[str(ctx.author.id)] = []
                await ctx.respond("All notes deleted!", ephemeral=True)
            elif 1 <= index <= len(user_notes):
                del user_notes[index - 1]
                notes[str(ctx.author.id)] = user_notes
                await ctx.respond(f"Note {index} deleted!", ephemeral=True)
            else:
                await ctx.respond("Invalid note index!", ephemeral=True)

            with open("notes.json", "w") as f:
                json.dump(notes, f, indent=4)
        else:
            await ctx.respond("You have no notes!", ephemeral=True)
        await command_topper(ctx)
        logging_command(ctx, index)


    @bot.slash_command(name="feedback", description="Send feedback")
    #feedback_type options: bug, feature, other
    #feedback_feature options: commands, events, other
    

    async def send_bot_owner_feedback(ctx,
        feedback_type: discord.Option(str, choices=["Bug Report", "Feature Request", "Other"], description="What are you reporting?") = None,
        feedback_feature: discord.Option(str, choices=["Command", "Profile", "Other"], description="What feature is this about?") = None,
        feedback_description: discord.Option(str, description="Describe the issue / change") = None
    ):
            botOwner = bot.get_user(512609720885051425)
            embed = discord.Embed(title="Bot Owner Notification", description=f"**{ctx.author.name}#{ctx.author.discriminator}** has submitted feedback", color=discord.Color.red())
            embed.add_field(name="Feedback Type", value=feedback_type, inline=False)
            embed.add_field(name="Feedback Feature", value=feedback_feature, inline=False)
            embed.add_field(name="Feedback Description", value=feedback_description, inline=False)
            embed.set_footer(text=f"User ID: {ctx.author.id}")
            await botOwner.send(embed=embed)
            await ctx.respond("Thanks, Feedback has been sent!", ephemeral=True)


    @bot.slash_command(name="help", description="Get help")
    async def help_command(ctx):
        """Get help"""
        embed = discord.Embed(title="Help", color=discord.Color.green())
        embed.add_field(name="image-to-gif", value="Convert an image to a gif", inline=False)
        embed.add_field(name="video-to-gif", value="Convert a video to a gif", inline=False)
        embed.add_field(name="speech-bubble", value="Add a speech bubble to an image", inline=False)
        embed.add_field(name="impact", value="Add impact text to an image", inline=False)
        embed.add_field(name="urban", value="Search urban dictionary", inline=False)
        embed.add_field(name="urban-random-word", value="Get a random word from urban dictionary", inline=False)
        embed.add_field(name="units", value="Convert units", inline=False)
        embed.add_field(name="new-note", value="Create a new note", inline=False)
        embed.add_field(name="edit-note", value="Edit an existing note", inline=False)
        embed.add_field(name="my-notes", value="Read your notes", inline=False)
        embed.add_field(name="delete-note", value="Delete a note", inline=False)
        embed.add_field(name="feedback", value="Send feedback", inline=False)
        embed.add_field(name="help", value="Get help", inline=False)
        embed.add_field(name="invite", value="Invite the bot", inline=False)
        embed.add_field(name="vote", value="Vote for the bot and claim a reward", inline=False)
        await ctx.respond(embed=embed)
        await command_topper(ctx)
        logging_command(ctx)


    @bot.slash_command(name="vote", description="Vote for the bot and claim a reward")
    async def vote(ctx):
        topggID=1098280039486849174
        # Check if the user has voted on top.gg
        headers = {'Authorization': TOP_GG_TOKEN}
        request = requests.get(f"https://top.gg/api/bots/{topggID}/check?userId={ctx.author.id}", headers=headers)
        if request.status_code == 200:
            data = request.json()
            if data['voted'] == 1:
                await ctx.respond("Thanks for voting!")
                edit_user_data(ctx.author, "votes", get_user_data(ctx.author, "votes") + 1)
                #give VoteReward role
                try:
                    if discord.utils.get(ctx.guild.roles, name="Vote Reward") is None:
                        await ctx.guild.create_role(name="Vote Reward", color=discord.Color.nitro_pink())
                    await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name="Vote Reward"))
                    await ctx.respond("You have been given the Vote Reward role!")
                except discord.Forbidden:
                    pass
                    # await ctx.respond("I don't have permission to give you the Vote Reward role!")

            else:
                await ctx.respond(f"You haven't voted yet!\nhttps://top.gg/bot/{topggID}/vote")
        else:
            await ctx.respond("Error checking vote status!")
        await command_topper(ctx)


    @bot.event
    async def on_ready():
        print('Bot is now online')
        log.info(f"Bot is now online")

    @bot.event
    async def on_message(message):
        botOwner = bot.get_user(512609720885051425)  # Get the bot owner
        #messageAuthor = message.author.id # Get the author of the message
        #messageAuthor = bot.get_user(messageAuthor) # Get the specific author
        if message.guild != None: # Any message in a server
            logging_message(message)
            #read how many messages the user has sent and add 1
            edit_user_data(message.author, "messages", get_user_data(message.author, "messages") + 1)
            #add their username and discriminator
            edit_user_data(message.author, "username", message.author.name + "#" + message.author.discriminator)

            #if any keyword in keywords list is in the message content
            if any(keyword in message.content.lower() for keyword in keywords):
                embed=discord.Embed(title="Message Link Detected", url=message.jump_url, color=discord.Color.blue())
                embed.add_field(name="Message", value=message.content, inline=False)
                embed.add_field(name="Channel", value=message.channel, inline=False)
                embed.add_field(name="User", value=message.author, inline=False)

                await botOwner.send(embed=embed)


        # (A DM from a user) Check if the message is not from the bot or the bot owner 
        if message.author != bot.user and message.author != botOwner and message.guild == None:
            embed = discord.Embed(title="Message From", color=discord.Color.green())
            embed.add_field(name="User", value=message.author)
            embed.add_field(name="Message", value=message.content)
            try:
                urls = []
                for i in range(len(message.attachments)):
                    urls.append(message.attachments[i].url)
                embed.add_field(name="Attachment URLs", value='\n'.join(urls))
            except IndexError:
                pass
            try:
                #copy image link from message attachment
                embed.set_image(url=message.attachments[0].url)
            except IndexError:
                pass
            embed.add_field(name="UserID", value=message.author.id)

            await botOwner.send(embed=embed)

        # (Reply to DMs) If the message is from the botOwner and a reply to an embed message, get the user from the embed and send the message to them 
        if message.author == botOwner and message.reference:
            try:
                #from the reference, get the embed message
                messageReference = message.reference.message_id
                #get the embed in the message reference
                messageReference = await message.channel.fetch_message(messageReference)
                #get the user id from the embed
                messageReference = messageReference.embeds[0].fields[3].value
                #get the user from the user id
                messageReference = bot.get_user(int(messageReference))
                #send the message to the user
                await messageReference.send(message.content)
            except IndexError:
                pass

        # (!invites secret command)
        if message.author == botOwner and message.content.startswith("!invites"):
            guilds = await get_guild_invite(bot)
            guildNames = guilds[0]
            guildInvites = guilds[1]
            guildInfo = guilds[2]
            embed=discord.Embed(title="Guild Invites", color=discord.Color.green())
            #add a column for guild name and guild invite and guild info
            for i in range(len(guildNames)):
                embed.add_field(name=guildNames[i], value=f"Invite: {guildInvites[i]}\n{guildInfo[i]}", inline=False)
            await botOwner.send(embed=embed)
            
    bot.run(TOKEN)

if __name__ == "__main__":
    main()