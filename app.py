import os
import random
import logging as log
import time
import discord
import toml
import asyncio
import tracemalloc
from PIL import Image, ImageSequence
import requests
import ffmpeg
import yt_dlp

MESSAGE = 25
DIRECT_MESSAGE = 30
COMMAND = 35

# Define custom log level names
log.addLevelName(MESSAGE, "MESSAGE")
log.addLevelName(DIRECT_MESSAGE, "DIRECT_MESSAGE")
log.addLevelName(COMMAND, "COMMAND")

# Configure the logger
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode="a", filename="app.log")

# Create custom log functions
def log_message(msg):
    log.log(MESSAGE, msg)

def log_direct_message(msg):
    log.log(DIRECT_MESSAGE, msg)

def log_command(msg):
    log.log(COMMAND, msg)

tokenFile = "token.toml"
with open(tokenFile) as toml_file:
    data = toml.load(toml_file)
    TOKEN = data["token"]
    log.debug(f"Token read from '{tokenFile}'")

#if there is no temp folder make one
if not os.path.exists("temp"):
    os.makedirs("temp")

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

async def permission_notify(ctx):
    if ctx.guild == None:
        return
    if read_toml_var("permissionsInt") != ctx.guild.me.guild_permissions.value:
        await ctx.respond(f"One or more permissions are not enabled which may cause errors, please consider using /update-permissions", ephemeral=True)

def convert_image_to_gif(image_link, outputFormat = "gif"):
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
    image.save(output_path, format={outputFormat}, save_all=True)
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

def add_speech_bubble(image_link, speech_bubble_y_scale = 0.2):
    clean_up_temp_files()
    """
    Add a speech bubble to the top of the image or each frame of a GIF.
    """
    speechBubble = Image.open("assets/speechBubble.png").convert("RGBA")
    
    image_seed = random.randint(10000, 99999)
    output_path = f"temp/image{image_seed}.gif"

    # Download the image
    with open(f"temp/image{image_seed}.gif", "wb") as f:
        f.write(requests.get(image_link).content)

    image = Image.open(f"temp/image{image_seed}.gif")

    # Check if the image is a GIF
    if image.is_animated:
        frames = []
        for frame in ImageSequence.Iterator(image):
            frame = frame.convert("RGBA")
            bubble_height = int(frame.size[1] * speech_bubble_y_scale)  # Calculate bubble height as 20% of the image height
            speechBubble_resized = speechBubble.resize((frame.size[0], bubble_height))
            frame.paste(speechBubble_resized, (0, 0), speechBubble_resized)
            frames.append(frame)
        frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0)
    else:
        image = image.convert("RGBA")
        bubble_height = int(image.size[1] * speech_bubble_y_scale)  # Calculate bubble height as 20% of the image height
        speechBubble_resized = speechBubble.resize((image.size[0], bubble_height))
        image.paste(speechBubble_resized, (0, 0), speechBubble_resized)
        image.save(output_path, format="GIF", save_all=True)

    image.close()
    speechBubble.close()

    return output_path

def main():
    log.debug("Starting Main()")
    #Permissions Integer: 57598266564160
    bot = discord.Bot(intents=discord.Intents.all())
    log.debug("Bot object created")

    @bot.slash_command(name="log", description="Get the log file")
    async def log_command(
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

    @bot.slash_command(name="image-to-gif", description="Take an image link and send it as a gif")
    async def image_to_gif_command(ctx: discord.ApplicationContext, image_link: str):
        await ctx.respond(f"Converting image to gif... ") # this message will be deleted when the gif is sent
        try:
            newGif = convert_image_to_gif(image_link)
            await ctx.edit(content = f"Here is your gif!" , file=discord.File(newGif))
            os.remove(newGif)
        except Image.UnidentifiedImageError:
            await ctx.edit(content = f"Sorry, but that image link is invalid!")
        except AttributeError:
            await ctx.edit(content = f"Sorry, that is already a gif!")
        await permission_notify(ctx)

    @bot.slash_command(name="video-to-gif", description="Take a video link and send it as a gif")
    async def video_to_gif_command(
        ctx: discord.ApplicationContext,
        video_link: str,
        fps: discord.Option(int, "The FPS of the gif", required=False, default=20),
        scale: discord.Option(int, "The scale of the gif", required=False, default=320),
    ):
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
        except Exception as e:
            await ctx.edit(content = f"Sorry, but that video link is invalid!", ephemeral=True)
        await permission_notify(ctx)

    @bot.slash_command(name="speech-bubble", description="Add a speech bubble to an image")
    async def speech_bubble_command(
        ctx: discord.ApplicationContext,
        image_link: str,
        speech_bubble_size: discord.Option(float, "The size of the speech bubble in the y axis", required=False, default=0.2),
    ):
        if speech_bubble_size > 1 or speech_bubble_size < 0:
            await ctx.respond(f"Sorry, values between 0 and 1 only!", ephemeral=True)
            return
        await ctx.respond(f"Adding speech bubble to image... ")
        try:
            newImage = add_speech_bubble(image_link, speech_bubble_size)
            await ctx.edit(content = (f"Here is your image!") , file=discord.File(newImage))
            os.remove(newImage)
        except Exception as e:
            print (e)
            await ctx.edit(content = f"Sorry, but that image link is invalid!")
        await permission_notify(ctx)

    @bot.slash_command(name="update-permissions", description="Update the bot's permissions")
    async def update_permissions(ctx):
        if ctx.guild == None:
            await ctx.respond(f"Sorry, but this command can only be used in a server!", ephemeral=True)
            return
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        #get permissions in the current guild
        permissionIntents = ctx.guild.me.guild_permissions.value
        if permissionIntents == read_toml_var("permissionsInt"):
            await ctx.respond(f"Permissions are already up to date!", ephemeral=True)
            return
        #get invite link
        #set permission value of bot to the permissions from the toml file
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={read_toml_var('permissionsInt')}"
        await ctx.respond(f"{inviteLink}", ephemeral=True)

    @bot.event
    async def on_ready():
        print('Bot is now online')
        log.info(f"Bot is now online")
    
    @bot.event
    async def on_message(message):
        try:
            log_message(f"SERVER: '{message.guild.name}' ({message.guild.id}) | '{message.author.name}#{message.author.discriminator}' SAID: '{message.content}' WITH MESSAGE ATTACHMENTS: {message.attachments}")
        except AttributeError:
            log_direct_message(f"{message.author.name}#{message.author.discriminator}' SAID: '{message.content}' WITH MESSAGE ATTACHMENTS: {message.attachments}")

        #send any direct messages the bot gets to the bot owner
        if message.guild == None:
            if message.author.id == bot.user.id or message.author.id == 512609720885051425:
                return
            await bot.get_user(512609720885051425).send(f"DM FROM '{message.author.name}#{message.author.discriminator}': {message.content} {message.attachments}")


    bot.run(TOKEN)

if __name__ == "__main__":
    main()