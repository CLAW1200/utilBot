# the longer i spend on this, the more jank it becomes...
import utilityBeltLib as ub
import discord
from discord.ui import View
import os
import random
import logging
from PIL import Image
import requests
import urllib.parse
import aiohttp
from pint import UnitRegistry
import json
import csv
import hashlib
import base64
import codecs
import asyncio
import datetime
# Create a log
log = logging.getLogger('Utility Belt')

# Add custom levels
log.BOT_GOT_MESSAGE = lambda bot_message: log.log(25, f"GOT MESSAGE: {bot_message}")
log.BOT_GOT_COMMAND = lambda bot_command: log.log(25, f"GOT COMMAND: {bot_command}")

log.BOT_REPLY = lambda bot_message: log.log(25, f"SENT REPLY: {bot_message}")
log.BOT_MESSAGE = lambda bot_message: log.log(25, f"SENT MESSAGE: {bot_message}")

log.BOT_REPLY_SUCCESS = lambda bot_message: log.log(25, f"SUCCESS: {bot_message}")
log.BOT_REPLY_FAIL = lambda bot_message: log.log(25, f"FAIL: {bot_message}")

log.BOT_PROCESS = lambda bot_message: log.log(25, f"PROCESS: {bot_message}")


# Create a formatter and set it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

# Set the base level of the log
log.setLevel(logging.DEBUG)

# Create a console handler and set the level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # The level of logs to display in console
console_handler.setFormatter(formatter)

# Create a file handler and set the level to DEBUG
file_handler = logging.FileHandler('data/app.log')
file_handler.setLevel(logging.INFO) # The level of logs to display in file
file_handler.setFormatter(formatter)


# Add the file handler to the log
log.addHandler(file_handler)

# Add the console handler to the log
log.addHandler(console_handler)


def main():
    ureg = UnitRegistry()
    log.BOT_GOT_MESSAGE("Starting bot...")

    ########################
    # DECLARE VARIABLES HERE
    ########################
    keywords = {
        "https://discord",
    }
    BOT_TOKEN, TOP_GG_TOKEN, TOP_GG_ID = ub.get_tokens("config/token.toml")
    log.debug(f"Fetched bot token: **********")
    log.debug(f"Fetched top.gg token: **********")

    loading_emoji = ub.read_toml_var("loading_emoji")
    success_emoji = ub.read_toml_var("success_emoji")
    error_emoji = ub.read_toml_var("error_emoji")

    ########################
    ########################


    #if there is no temp folder make one
    if not os.path.exists("temp"):
        log.info("Creating temp folder as it does not exist")
        os.makedirs("temp")
        log.info("Created temp folder")
    else:
        log.debug("Temp folder already exists")

    intents = discord.Intents.all()  # Create an intents object with default intents
    intents.message_content = False  # Disable the message content intent
    intents.typing = False  # Disable the typing intent
    intents.presences = False  # Disable the presence intent
    bot = discord.Bot(intents=intents)
    log.info(f"Created bot object: {bot}\n with intents: {intents}\n")

    from discord.ext import tasks, commands

    class logDataToCSV(commands.Cog):
        def __init__(self, bot):
            self.index = 0
            self.bot = bot
            self.printer.start()

        def cog_unload(self):
            self.printer.cancel()

        @tasks.loop(seconds=60)
        async def printer(self):
            log.debug(f"Checking time")
            now = datetime.datetime.now()
            if now.minute == 0: 
                await ub.log_data_to_csv(self.bot)
                log.info(f"Logged data to CSV")

        @printer.before_loop
        async def before_printer(self):
            print('waiting...')
            await self.bot.wait_until_ready()

    logDataToCSV(bot)

    def check_bot_permissions(ctx):
        if ctx.guild == None:
            return True
        
        binary_guild_permissions = bin(ctx.guild.me.guild_permissions.value)
        binary_required_permissions = bin(ub.read_toml_var("permissionsInt"))

        #perform binary AND operation on the two binary strings
        check = int(binary_guild_permissions, 2) & int(binary_required_permissions, 2)
        if check == int(binary_required_permissions, 2):
            return True
        else:
            return False

    def command_ban_check(ctx):
        # Check banned users file, If user is banned, return True
        try:
            with open("config/banned_users.json", "r") as f:
                banned_users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log.error("Failed to load banned users file")
            banned_users = []
        if ctx.author.id in banned_users:
            log.BOT_REPLY_FAIL(f"Blocked command from {ctx.author.name}#{ctx.author.discriminator} due to being BANNED")
            return True

    async def check_if_user_has_premium(user):
        info = await bot.fetch_entitlements()
        #check in list and find index for ctx.author.id 
        for ent in info:
            if ent.user_id == user.id and ent.starts_at < datetime.datetime.now(datetime.timezone.utc) < ent.ends_at:
                print (ent)
                return True
        return False
        
    async def command_topper(ctx):

        ub.edit_user_data(ctx.author, "commandsUsed", ub.get_user_data(ctx.author, "commandsUsed") + 1)
        ub.edit_user_data(ctx.author, "username", ctx.author.name + "#" + ctx.author.discriminator)
        if ub.get_user_data(ctx.author, "commandsUsed") <= 1:
            await ctx.respond(f"Welcome to Utility Belt! You can use **/help** to get a list of commands.\nPlease use **/feedback** if you have any issues!\nRemember to use **/vote** if you find me useful :) - This will be the only reminder", ephemeral=True)
            log.BOT_REPLY(f"Sent welcome message to {ctx.author.name}#{ctx.author.discriminator}")

        if not check_bot_permissions(ctx):
            await ctx.respond("Warning: I am missing some permissions which may cause errors. Please use /update-permissions to avoid problems with commands", ephemeral=True)
            log.BOT_REPLY(f"Sent missing permissions message to {ctx.author.name}#{ctx.author.discriminator}")
            return False
        return True

    @bot.slash_command(name="image-to-gif", description="Take an image link and send it as a gif")
    async def image_to_gif_command(ctx: discord.ApplicationContext, image_link: str):
        if command_ban_check(ctx):
            return
        
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} image_link = {image_link}")

            if "https://discord.com/channels/" in image_link:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link, not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to invalid image link of {image_link}")
                return
            
            try:
                imageFileSize = ub.get_file_size(image_link)
                if imageFileSize > ub.read_toml_var("maxFileSize"):
                    await ctx.respond(f"Sorry, but the max image size is {ub.read_toml_var('maxFileSize')/1000000}MB! {error_emoji}", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to file size of {imageFileSize}")
                    return
            except Image.UnidentifiedImageError as e:
                await ctx.edit(content = f"Sorry, but that image link is invalid! {error_emoji}")
                await ctx.respond(content = f"Sorry, due to the new Discord changes regarding CDN links I cannot access that image.\nCopying the link again from the image may fix this.\n**We are currently working on a fix for this and it should be resolved soon.**\nPlease see [this post](https://www.reddit.com/r/DataHoarder/comments/16zs1gt/cdndiscordapp_links_will_expire_breaking/) to learn more. {error_emoji}", ephemeral=True, embed=None)
                log.error(e)
            except Exception as e:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link, not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to invalid image link of {image_link}")
                log.error(e)
                return

            await ctx.respond(f"Converting image to gif {loading_emoji}") # this message will be edited when the gif is sent
            log.BOT_PROCESS(f"Converting image {image_link} to gif")
            try:
                newGif = ub.convert_image_to_gif(image_link)
                await ctx.edit(content = f"Here is your gif! {success_emoji}" , file=discord.File(newGif))
                log.BOT_REPLY_SUCCESS(f"Converted image {image_link}")
            except Image.UnidentifiedImageError as e:
                await ctx.edit(content = f"Sorry, but that image link is invalid! {error_emoji}")
                log.error(e)
            await command_topper(ctx)

    @bot.slash_command(name="video-to-gif", description="Take a video link and send it as a gif")
    async def video_to_gif_command(
        ctx: discord.ApplicationContext,
        video_link: str,
        fps: discord.Option(int, "The FPS of the gif", required=False, default=25), # type: ignore
        scale: discord.Option(int, "The scale of the gif", required=False), # type: ignore
    ):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked video-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return

        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} video_link = {video_link}")

            if "https://discord.com/channels/" in video_link:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link, not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to invalid image link of {video_link}")
                return
            #do not download videos larger than maxFileSize
            try:
                videoFileSize = ub.get_file_size(video_link)
                if videoFileSize > 8000000:
                    await ctx.respond(f"Sorry, but the max video size is 8MB! {error_emoji}", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Blocked video-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to file size of {videoFileSize}")
                    return

            except Exception as e:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked video-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to invalid video link of {video_link}")
                log.error(e)
                return

            if fps > 30:
                await ctx.respond(f"Sorry, but the max FPS is 30! {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked video-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to FPS of {fps}")
                return
            if scale != None:
                if scale > 500:
                    await ctx.respond(f"Sorry, but the max scale is 500px! {error_emoji}", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Blocked video-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to scale of {scale}")
                    return
            
            await ctx.respond(f"Converting video to gif... {loading_emoji}")
            log.BOT_PROCESS(f"Converting video {video_link} to gif")
            try:
                newGif = ub.convert_video_to_gif(video_link, fps, scale)
                await ctx.edit(content = f"Here is your gif! {success_emoji}" , file=discord.File(newGif))
                log.BOT_REPLY_SUCCESS(f"Converted video {video_link} to gif")

            except discord.errors.HTTPException as e:
                await ctx.edit(content = f"Sorry, but the converted video is too large for discord or your server! {error_emoji}")
                log.error(e)
            except Exception as e:
                await ctx.edit(content = f"Sorry, but that video link is invalid! {error_emoji}")
                log.error(e)
            await command_topper(ctx)

    @bot.slash_command(name="speech-bubble", description="Add a speech bubble to an image or gif")
    async def speech_bubble_command(
        ctx: discord.ApplicationContext,
        image_link: str,
        speech_bubble_size: discord.Option(float, "The size of the speech bubble in the y axis", required=False, default=0.2), # type: ignore
    ):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked speech-bubble command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} image_link = {image_link} speech_bubble_size = {speech_bubble_size}")

            if "https://discord.com/channels/" in image_link:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link, not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked image-to-gif command from {ctx.author.name}#{ctx.author.discriminator} due to invalid image link of {image_link}")
                return

                
            #do not download videos larger than maxFileSize
            try:
                imageFileSize = ub.get_file_size(image_link)
                if imageFileSize > ub.read_toml_var("maxFileSize"):
                    await ctx.respond(f"Sorry, but the max image size is {ub.read_toml_var('maxFileSize')/1000000}MB! {error_emoji}", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Blocked speech-bubble command from {ctx.author.name}#{ctx.author.discriminator} due to file size of {imageFileSize}")
                    return
            except Exception as e:
                await ctx.respond(f"Sorry, but that image link is invalid! {error_emoji}\nMake sure your using an image link not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked speech-bubble command from {ctx.author.name}#{ctx.author.discriminator} due to invalid image link of {image_link}")
                log.error(e)
                return
            
            if speech_bubble_size > 1 or speech_bubble_size < 0:
                await ctx.respond(f"Sorry, values between 0 and 1 only! {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked speech-bubble command from {ctx.author.name}#{ctx.author.discriminator} due to speech bubble size of {speech_bubble_size}")
                return
            
            await ctx.respond(f"Adding speech bubble to image {loading_emoji}")
            log.BOT_PROCESS(f"Adding speech bubble to image {image_link}")
            try:
                newImage = ub.add_speech_bubble(image_link, speech_bubble_size)
                await ctx.edit(content = (f"Here is your image! {success_emoji}") , file=discord.File(newImage))
                log.BOT_REPLY_SUCCESS(f"Added speech bubble to image {image_link}")
            # cannot identify image file
            except Image.UnidentifiedImageError as e:
                await ctx.edit(content = f"Sorry, but that image link is invalid! {error_emoji}")
                await ctx.respond(content = f"Sorry, due to the new Discord changes regarding CDN links I cannot access that image.\nCopying the link again from the image may fix this.\n**We are currently working on a fix for this and it should be resolved soon.**\nPlease see [this post](https://www.reddit.com/r/DataHoarder/comments/16zs1gt/cdndiscordapp_links_will_expire_breaking/) to learn more. {error_emoji}", ephemeral=True, embed=None)
                log.error(e)
            except Exception as e:
                await ctx.edit(content = f"Sorry, but I could not add a speech bubble to that image! {error_emoji}")
                log.BOT_REPLY_FAIL(f"Failed to add speech bubble to image {image_link}")
                log.error(e)
            try:
                # os.remove(newImage)
                log.BOT_PROCESS(f"Removed temporary file {newImage}")
            except Exception as e:
                log.error(e)
            await command_topper(ctx)

    @bot.slash_command(name="download", description="Download from Youtube, SoundCloud, Twitter, Instagram and more!")
    async def download_command(ctx: discord.ApplicationContext, 
                                media_link: str,
                                audio_only: discord.Option(bool, "Whether to download audio only", required=False, default=False), # type: ignore # type: ignore
                                video_quality: discord.Option(str, choices=["max", "144", "240", "360", "480", "720", "1080", "1440", "2160"], required=False, default="360"), # type: ignore
                                audio_quality: discord.Option(str, choices=["best", "mp3", "wav", "ogg", "opus"], required=False, default="mp3") # type: ignore
                               ):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked download command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} media_link = {media_link} audio_only = {audio_only} video_quality = {video_quality} audio_quality = {audio_quality}")

            if "https://discord.com/channels/" in media_link:
                await ctx.respond(f"Sorry, but that media link is invalid! {error_emoji}\nMake sure your using a media link, not a message link.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked play command from {ctx.author.name}#{ctx.author.discriminator} due to invalid media link of {media_link}")
                return
            
            if (video_quality != ("360" or "240" or "144")) and not await check_if_user_has_premium(ctx.author):
                await ctx.respond(f"Sorry, but only 360p, 240p and 144p are available for non-premium users! Please upgrade to Utility Belt+ to get access to better quality downloads and other features. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked download command from {ctx.author.name}#{ctx.author.discriminator} due to quality of {video_quality}")
                return
            
            if (audio_quality != "mp3") and not await check_if_user_has_premium(ctx.author):
                await ctx.respond(f"Sorry, but only mp3 is available for non-premium users! Please upgrade to Utility Belt+ to get access to better quality downloads and other features. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Blocked download command from {ctx.author.name}#{ctx.author.discriminator} due to quality of {audio_quality}")
                return
            
            await ctx.respond(f"Downloading media... {loading_emoji}")

            try:
                file = ub.download_multimedia(media_link, audio_only, video_quality, audio_quality)
                if file == None:
                    await ctx.edit(content = f"Sorry, but that media link is invalid! {error_emoji}")
                    log.BOT_REPLY_FAIL(f"Failed to download media from {media_link}")
                    return
                await ctx.edit(content = f"Here is your media! {success_emoji}", file=discord.File(file))
                log.BOT_REPLY_SUCCESS(f"Downloaded media from {media_link}")
            except discord.errors.HTTPException as e:
                await ctx.edit(content = f"Sorry, but that media is too large for discord! Try lowering the quality. {error_emoji}")
                log.BOT_REPLY_FAIL(f"Failed to download media from {media_link}")
                log.error(e)            
            except Exception as e:
                await ctx.edit(content = f"It seems like this service is not supported yet or your link is invalid. Have you pasted the right link? {error_emoji}")
                log.BOT_REPLY_FAIL(f"Failed to download media from {media_link}")
                log.error(e)

    @bot.slash_command(name="update-permissions", description="Update the bot's permissions")
    async def update_permissions(ctx):
        log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
        if ctx.guild == None:
            await ctx.respond(f"Sorry, but this command can only be used in a server!", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked update-permissions command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        if check_bot_permissions(ctx):
            await ctx.respond(f"Permissions are already up to date!", ephemeral=True)
            log.BOT_REPLY_SUCCESS(f"Permissions are already up to date")
            return
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={ub.read_toml_var('permissionsInt')}"
        await ctx.respond(f"{inviteLink}", ephemeral=True)
        log.BOT_REPLY_SUCCESS(f"Sent invite link to {ctx.author.name}#{ctx.author.discriminator}")
        await command_topper(ctx)

    @bot.slash_command(name="invite", description="Get the bot's invite link")
    async def invite_command(ctx):
        log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
        #respond with message with button that links to bot invite link
        try:
            client_id = bot.user.id
            inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={ub.read_toml_var('permissionsInt')}"
            await ctx.respond(f"{inviteLink}", ephemeral=True)
            await command_topper(ctx)
        except Exception as e:
            log.error(f"Shit must really going wrong now!\n{e}")

    @bot.slash_command(name="urban", description="Find a definition of a word on urban dictionary")
    async def urban_command(
        ctx: discord.ApplicationContext,
        word: str,
        random_result: discord.Option(bool, "Whether to get a random result", required=False, default=False), # type: ignore
        ):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked urban command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Fetches the definition of a word from Urban Dictionary."""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} /{ctx.command} word = {word} random_result = {random_result}")
            try:
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
                        log.BOT_REPLY_SUCCESS(f"Sent definition of {word}")

            except Exception as e:
                await ctx.respond(f"Failed to send definition of {word}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to send definition of {word}")
                log.error(f"Its all gone wrong!\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="urban-random-word", description="Get a random word from urban dictionary")
    async def random_word_command(ctx):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked urban-random-word command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Gets a random word from Urban Dictionary."""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
            try:
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
                        log.BOT_REPLY_SUCCESS(f"Sent random word {word}")
                
            except Exception as e:
                await ctx.respond(f"Failed to send random word", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to send random word")
                log.error(f"This is bad :(\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="units", description="Convert units")
    async def convert(ctx, value: float, unit_from: str, unit_to: str):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked units command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} value = {value} unit_from = {unit_from} unit_to = {unit_to}")
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
                log.BOT_REPLY_SUCCESS(f"Sent units conversion")

            except Exception as e:
                await ctx.respond(f"{str(e)}")
                log.BOT_REPLY_FAIL(f"Failed to send units conversion")
                log.error(f"Oh no\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="note-new", description="Write a new note")
    async def new_note_command(ctx, note: str):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked note-new command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Create a new note for the user"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} note = {note}")
            try:
                notes = {}

                try:
                    with open("data/notes.json", "r") as f:
                        notes = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                user_notes = notes.get(str(ctx.author.id), [])
                user_notes.append(note)
                notes[str(ctx.author.id)] = user_notes

                with open("data/notes.json", "w") as f:
                    json.dump(notes, f, indent=4)

                await ctx.respond("New note added!\nSee your new note with /notes.", ephemeral=True)
                log.BOT_REPLY_SUCCESS(f"Added new note for {ctx.author.name}#{ctx.author.discriminator}")
            except Exception as e:
                await ctx.respond(f"Failed to add new note!", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to add new note for {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"This is not ideal\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="note-edit", description="Edit a note")
    async def edit_note_command(ctx, index: int, note: str):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked note-edit command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Edit an existing note for the user"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} index = {index} note = {note}")
            try:
                notes = {}

                try:
                    with open("data/notes.json", "r") as f:
                        notes = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                user_notes = notes.get(str(ctx.author.id), [])

                if user_notes:
                    undeleted_user_notes = [n for n in user_notes if "[X]" not in n]

                    if 1 <= index <= len(undeleted_user_notes):
                        undeleted_index = index - 1
                        edited_note = undeleted_user_notes[undeleted_index]
                        user_notes[user_notes.index(edited_note)] = note
                        notes[str(ctx.author.id)] = user_notes

                        with open("data/notes.json", "w") as f:
                            json.dump(notes, f, indent=4)

                        await ctx.respond(f"Note {index} updated!", ephemeral=True)
                        log.BOT_REPLY_SUCCESS(f"Edited note for {ctx.author.name}#{ctx.author.discriminator}")
                    else:
                        await ctx.respond("Invalid note index!", ephemeral=True)
                        log.BOT_REPLY_FAIL(f"Failed to edit note for {ctx.author.name}#{ctx.author.discriminator} due to invalid index of {index}")
                else:
                    await ctx.respond("You have no notes!", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to edit note for {ctx.author.name}#{ctx.author.discriminator} due to no notes")

            except Exception as e:
                await ctx.respond(f"Failed to edit note!", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to edit note for {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"what now?\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="notes", description="Read your notes")
    async def my_notes_command(ctx):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked notes command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Read the user's notes"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
            try:
                notes = {}
                try:
                    with open("data/notes.json", "r") as f:
                        notes = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                user_notes = notes.get(str(ctx.author.id), [])

                non_completed_notes = [note for note in user_notes if "[X]" not in note]

                if non_completed_notes:
                    formatted_notes = '\n'.join(f"{i+1}. {note}" for i, note in enumerate(non_completed_notes))
                    await ctx.respond(f"Your notes:\n{formatted_notes}", ephemeral=True)
                    log.BOT_REPLY_SUCCESS(f"Sent notes for {ctx.author.name}#{ctx.author.discriminator}")
                else:
                    await ctx.respond("You have no notes!", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to send notes for {ctx.author.name}#{ctx.author.discriminator} due to no notes")
            except Exception as e:
                await ctx.respond(f"Failed to send notes!", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to send notes for {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"AHHHH!\n{e}")
            await command_topper(ctx)

    @bot.slash_command(name="note-delete", description="Delete a note or leave index blank to delete all")
    async def delete_note_command(ctx, index: int = None):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked note-delete command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Delete a note, or all for the user"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} index = {index}")
            try:
                notes = {}

                try:
                    with open("data/notes.json", "r") as f:
                        notes = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                user_notes = notes.get(str(ctx.author.id), [])

                if user_notes:
                    if index is None:
                        for i, note in enumerate(user_notes):
                            if "[X]" not in note:
                                user_notes[i] = f"[X] {note}"
                        notes[str(ctx.author.id)] = user_notes
                        await ctx.respond("All notes deleted!", ephemeral=True)
                    elif 1 <= index <= len(user_notes):
                        undeleted_user_notes = [n for n in user_notes if "[X]" not in n]
                        undeleted_index = index - 1
                        try:
                            deleted_note = undeleted_user_notes[undeleted_index]
                        except IndexError:
                            await ctx.respond("Invalid note index!", ephemeral=True)
                            log.BOT_REPLY_FAIL(f"Failed to delete note for {ctx.author.name}#{ctx.author.discriminator} due to invalid index of {index}")
                            return
                        user_notes[user_notes.index(deleted_note)] = f"[X] {deleted_note}"
                        notes[str(ctx.author.id)] = user_notes
                        await ctx.respond(f"Note {index} deleted!", ephemeral=True)
                        log.BOT_REPLY_SUCCESS(f"Deleted note for {ctx.author.name}#{ctx.author.discriminator}")
                    else:
                        await ctx.respond("Invalid note index!", ephemeral=True)
                        log.BOT_REPLY_FAIL(f"Failed to delete note for {ctx.author.name}#{ctx.author.discriminator} due to invalid index of {index}")
                        return

                    with open("data/notes.json", "w") as f:
                        json.dump(notes, f, indent=4)
                else:
                    await ctx.respond("You have no notes!", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to delete notes for {ctx.author.name}#{ctx.author.discriminator} due to no notes")
                    return
            except Exception as e:
                await ctx.respond(f"Failed to delete notes!", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to delete notes for {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"{e}")
            await command_topper(ctx)

    @bot.slash_command(name="find-a-friend", description="Get a random discord user")
    async def dox_command(ctx):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked find-a-friend command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
            try:
                def get_random_user():
                    randomUser = bot.users[random.randint(0, len(bot.users))-1]
                    if randomUser == ctx.author or randomUser.bot:
                        return get_random_user()
                    else:
                        return randomUser
                await ctx.respond(f"Your new friend is `{get_random_user()}`")
                log.BOT_REPLY_SUCCESS(f"Sent random user to {ctx.author.name}#{ctx.author.discriminator}")
            except Exception as e:
                await ctx.respond(f"Failed to send a user!", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to send random user to {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"{e}")
            await command_topper(ctx)

    @bot.slash_command(name="timestamp", description="Convert a time to a timestamp")
    async def timestamp_command(ctx, 
                                date_time: discord.Option(str,
                                    description="Enter a Holiday or DateTime after 1/1/1970") = None, # type: ignore
                                output_format: discord.Option(str,
                                    choices=["Relative", "Short Time", "Long Time", "Short Date", "Long Date", "Long Date with Short Time", "Long Date with Day of the Week"], 
                                    description="The format of the timestamp", required=False, default="Relative") = "Relative"): # type: ignore
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked timestamp command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Convert a time to a timestamp"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} date_time = {date_time} output_format = {output_format}")
            timestamp = ub.timecode_convert(date_time, output_format)
            if timestamp == None:
                await ctx.respond(f"Sorry, but that time is invalid! Make sure the time is after <t:0:f> {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to convert time {date_time} to timestamp")
                return
            await ctx.respond(f"Your timestamp is {timestamp}")
            log.BOT_REPLY_SUCCESS(f"Converted time {date_time} to timestamp")
            await command_topper(ctx)

    @bot.slash_command(name="qr-code", description="Generate a qr code") # Text input. Then choose from image output or text output
    async def qr_code_command(ctx, 
                              text: discord.Option(str, 
                              description="Enter text to convert to a QR code") = None, # type: ignore
                              output: discord.Option(str, 
                              choices=["Image", "Text"], 
                              description="The output of the QR code", required=False, default="Image") = "Image"): # type: ignore
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked qr-code command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Generate a qr code"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} text = {text} output = {output}")
            if text == None:
                await ctx.respond(f"Sorry, but you need to enter some text! {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate QR code due to no text")
                return
            if output == "Image":
                try:
                    qrCode = ub.qr_code_image_generator(text)
                    await ctx.respond(f"Here is your QR code! {success_emoji}", file=discord.File(qrCode))
                    log.BOT_REPLY_SUCCESS(f"Generated QR code for {ctx.author.name}#{ctx.author.discriminator}")
                except Exception as e:
                    await ctx.respond(f"Sorry, but I could not generate a QR code! {error_emoji}", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to generate QR code for {ctx.author.name}#{ctx.author.discriminator}")
                    log.error(f"{e}")
            elif output == "Text":
                await ctx.respond(f"Here is your QR code! {success_emoji}\n`{ub.qr_code_text_generator(input=text)}`")
                log.BOT_REPLY_SUCCESS(f"Generated QR code for {ctx.author.name}#{ctx.author.discriminator}")
            await command_topper(ctx)    

    @bot.slash_command(name="imagine", description="AI Generate an image quickly")
    async def quick_imagine_command(ctx, 
                                    prompt: discord.Option(str, 
                                    description="Enter a prompt to generate an image from") = None, # type: ignore
                                    enhancer: discord.Option(str,
                                    choices=["None", "Digital Painting", "Indie Game", "Photo", "Film Noir", "Isometric Room", "Space Hologram", "Cute Creature", "Realistic Portrait", "Realistic Landscape"],
                                    description="The enhancer to use on the image", required=False, default="None") = "None", # type: ignore
                                    gif: discord.Option(bool,
                                    description="Whether to generate a gif or not", required=False, default=False) = False, # type: ignore
                                    img2img: discord.Option(str,
                                    description="Generate an image from another image (url)", required=False, default=None) = None, # type: ignore
                                    seed: discord.Option(int,
                                    description="The seed for the image generation", required=False, default=None) = None, # type: ignore
                                    strength: discord.Option(float,
                                    description="The strength of the image generation (0-1)", required=False, default=None) = None, # type: ignore
                                    steps: discord.Option(int,
                                    choices=[1, 2, 3, 4, 5, 6, 7, 8],
                                    description="The steps for the image generation (1-8)", required=False, default=None) = None # type: ignore
                                    ):
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked imagine command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """AI Generate an image quickly"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} prompt = {prompt} enhancer = {enhancer} gif = {gif} img2img = {img2img} seed = {seed} strength = {strength} steps = {steps}")
            if prompt == None:
                await ctx.respond(f"Sorry, but you need to enter a prompt! {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate image due to no prompt")
                return

            if img2img is not None and await check_if_user_has_premium(ctx.author) == False:
                await ctx.respond(f"Please upgrade to unlock Img2Img and extra generation settings. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate image due to no premium")
                return
            
            if seed is not None and await check_if_user_has_premium(ctx.author) == False:
                await ctx.respond(f"Please upgrade to unlock custom image seeds and extra generation settings. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate image due to no premium")
                return
            
            if strength is not None and await check_if_user_has_premium(ctx.author) == False:
                await ctx.respond(f"Please upgrade to unlock custom image generation strength and extra generation settings. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate image due to no premium")
                return
            
            if steps is not None and await check_if_user_has_premium(ctx.author) == False:
                await ctx.respond(f"Please upgrade to unlock custom image generation steps and extra generation settings. {error_emoji}", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to generate image due to no premium")
                return

            try:
                await ctx.respond(f"Generating image... {loading_emoji}")
                log.BOT_PROCESS(f"Generating image from prompt {prompt}")
                image = await ub.ai_image_gen(prompt, enhancer, img2img, seed, strength, steps)
                if gif == True:
                    #rename image to gif
                    os.rename(image, image.replace(".jpg", ".gif"))
                    image = image.replace(".jpg", ".gif")
                    
                await ctx.edit(content = f"Here is your image! {success_emoji}" , file=discord.File(image))
                log.BOT_REPLY_SUCCESS(f"Generated image for {ctx.author.name}#{ctx.author.discriminator}")

            except Exception as e:
                await ctx.edit(content = f"Sorry, but I could not generate an image! {error_emoji}")
                log.BOT_REPLY_FAIL(f"Failed to generate image for {ctx.author.name}#{ctx.author.discriminator}")
                log.error(f"{e}")
            await command_topper(ctx)
        
    @bot.slash_command(name="peepee", description="Get your peepee size")
    async def peepee_command(ctx, user: discord.Option(discord.User, description="User to get peepee size of") = None): # type: ignore
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked peepee command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Get your peepee size"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} user = {user}")
            #hash the user id to get a random number
            if user == None:
                user = ctx.author
            peepeeSize = int(hashlib.sha256(str(user.id).encode()).hexdigest(), 16) % 20 # get a random number between 0 and 19
            if user.id == ub.read_toml_var("botOwner"):
                peepeeSize = 20
            peepee = "8" + "=" * peepeeSize + "D"
            await ctx.respond(f"{user.mention} peepee size is {peepee}")
            log.BOT_REPLY_SUCCESS(f"Sent peepee size of {peepeeSize} to {ctx.author.name}#{ctx.author.discriminator}")
            await command_topper(ctx)

    ongoing_games = {}
    @bot.slash_command(name="rps", description="Play rock paper scissors with another user")
    async def rps_command(ctx, user: discord.Option(discord.User, description="User to play with") = None): # type: ignore
        if command_ban_check(ctx):
            return
        if ctx.guild == None:
            await ctx.respond("Sorry, but this command can only be used in a server!", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked rps command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        else:
            """Play rock paper scissors with another user"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} user = {user}")
            log.warning(f"A game of RPS is staring. Prepare for headaches")
            if user is None:
                await ctx.respond("Please mention a user to play with.", ephemeral=True)
                return

            if user == ctx.author:
                await ctx.respond("Sorry, you can't play with yourself ;)", ephemeral=True)
                return

            if user.bot:
                await ctx.respond("You can't play with a bot!", ephemeral=True)
                return

            game_key = tuple(sorted([ctx.author.id, user.id]))
            if game_key in ongoing_games:
                await ctx.respond("There is already an ongoing game involving these players.", ephemeral=True)
                return

            #create a list of games and append a new game to it
            ongoing_games[game_key] = RPSView(ctx.author, user)

            #send the message
            await ctx.respond(f"{user.mention}, you have been challenged to a game of Rock Paper Scissors by {ctx.author.mention}!\nBoth players, please select your move.", view=ongoing_games[game_key])
            log.BOT_REPLY_SUCCESS(f"Sent RPS game to {ctx.author.name}#{ctx.author.discriminator} and {user.name}#{user.discriminator}")
            ongoing_games[game_key].timer = bot.loop.create_task(ongoing_games[game_key].start_timer())

    class RPSView(View):
        def __init__(self, challenger, opponent):
            super().__init__(timeout=None)  # Explicitly call the parent class's __init__
            self.challenger = challenger
            self.opponent = opponent
            self.moves = {self.challenger.id: None, self.opponent.id: None}
            self.timer = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user in [self.challenger, self.opponent]

        async def start_timer(self):
            log.warning(f"Starting timer for RPS game between {self.challenger.name}#{self.challenger.discriminator} and {self.opponent.name}#{self.opponent.discriminator}")
            await asyncio.sleep(30)

            if None in self.moves.values():
                await self.on_timeout()
            else:
                # The game has already concluded, so no action needed
                pass

        @discord.ui.button(label="Rock 🗿", style=discord.ButtonStyle.primary, custom_id="rps_rock")
        async def rock_button(self, button: discord.Button, interaction: discord.Interaction):
            await self.process_move(button, interaction, "rock")

        @discord.ui.button(label="Paper 📰", style=discord.ButtonStyle.primary, custom_id="rps_paper")
        async def paper_button(self, button: discord.Button, interaction: discord.Interaction):
            await self.process_move(button, interaction, "paper")

        @discord.ui.button(label="Scissors ✂️", style=discord.ButtonStyle.primary, custom_id="rps_scissors")
        async def scissors_button(self, button: discord.Button, interaction: discord.Interaction):
            await self.process_move(button, interaction, "scissors")

        async def process_move(self, button, interaction, move):
            await interaction.response.defer(ephemeral=True)
            log.warning("here we go again")

            if interaction.user == self.challenger and self.moves[self.challenger.id] is None:
                self.moves[self.challenger.id] = move
            elif interaction.user == self.opponent and self.moves[self.opponent.id] is None:
                self.moves[self.opponent.id] = move
            else:
                return

            if None not in self.moves.values():
                await self.send_results(interaction)

        async def send_results(self, interaction):
            # Stop the timer since the game has concluded
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None  # Reset the timer

            # Compare the moves and determine the winner
            winner = determine_winner(self.moves[self.challenger.id], self.moves[self.opponent.id])

            # Prepare the result message mentioning the winner and the choices
            if winner == "tie":
                result_message = f"⛔ It's a tie!\n\n{self.challenger.mention} chose {self.moves[self.challenger.id]}.\n{self.opponent.mention} chose {self.moves[self.opponent.id]}."
            else:
                winner = self.challenger if winner == self.moves[self.challenger.id] else self.opponent
                result_message = f"🎉 {winner.mention} wins!\n\n{self.challenger.mention} chose {self.moves[self.challenger.id]}.\n{self.opponent.mention} chose {self.moves[self.opponent.id]}."

            # Edit the message with the result
            await self.message.edit(content=result_message, view=None)
            log.BOT_REPLY_SUCCESS(f"Sent RPS results to {self.challenger.name}#{self.challenger.discriminator} and {self.opponent.name}#{self.opponent.discriminator}")

            # Remove the game from the ongoing games
            game_key = tuple(sorted([self.challenger.id, self.opponent.id]))
            del ongoing_games[game_key]

        async def on_timeout(self):
            # Reset the moves
            self.moves = {self.challenger.id: None, self.opponent.id: None}

            #if game is not over, edit message to say game is over
            if self.timer is not None:
                # Edit the message to reflect the expiration
                expiration_message = f"⌛ The game between {self.challenger.mention} and {self.opponent.mention} has expired."
                await self.message.edit(content=expiration_message, view=None)
                log.BOT_REPLY_SUCCESS(f"Sent RPS timeout message to {self.challenger.name}#{self.challenger.discriminator} and {self.opponent.name}#{self.opponent.discriminator}")

            # Remove the game from the ongoing games
            game_key = tuple(sorted([self.challenger.id, self.opponent.id]))
            del ongoing_games[game_key]

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            # Only allow the two players to interact with the buttons
            return interaction.user in [self.challenger, self.opponent]

        async def on_error(self, error, item, traceback):
            log.error(f"I am going to bash my head into a wall\n{error}")
            # Handle errors and cancel the timer
            if isinstance(error, discord.NotFound):
                self.timer.cancel()

    def determine_winner(move1, move2):
        if move1 == move2:
            return "tie"
        elif move1 == "rock":
            if move2 == "paper":
                return "paper"
            else:
                return "rock"
        elif move1 == "paper":
            if move2 == "scissors":
                return "scissors"
            else:
                return "paper"
        elif move1 == "scissors":
            if move2 == "rock":
                return "rock"
            else:
                return "scissors"

    @bot.slash_command(name="encode", description="Encode a message")
    async def encode_command(ctx,
                            message: discord.Option(str, description="Message to encode") = None, # type: ignore
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Encode mode") = None, # type: ignore
                            key: discord.Option(str, description="Key to encode with") = None, # type: ignore
                            hide: discord.Option(bool, description="Hide the message") = False): # type: ignore
        if command_ban_check(ctx):
            return
        
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked encode command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            """Encode a message"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} message = {message} mode = {mode} key = {key} hide = {hide}")
            if message is None:
                await ctx.respond("Please enter a message to encode.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to encode message for {ctx.author.name}#{ctx.author.discriminator} due to no message")
                return
            if mode is None:
                await ctx.respond("Please enter a mode to encode with.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to encode message for {ctx.author.name}#{ctx.author.discriminator} due to no mode")
                return

            encoded_message = None

            if mode == "base64":
                encoded_message = base64.b64encode(message.encode()).decode()
            elif mode == "rot13":
                encoded_message = codecs.encode(message, 'rot_13')
            elif mode == "caesar":
                if key is None or not key.isdigit():
                    await ctx.respond("Please enter a valid key for the Caesar cipher.", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to encode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid key of {key}")
                    return
                encoded_message = ub.caesar_cipher_encode(message, key)
            elif mode == "vigenere":
                if key is None:
                    await ctx.respond("Please enter a valid key for the Vigenère cipher.", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to encode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid key of {key}")
                    return
                encoded_message = ub.vigenere_cipher_encode(message, key)
            elif mode == "atbash":
                encoded_message = ub.atbash_cipher_encode(message)
            elif mode == "binary":
                encoded_message = ' '.join(format(ord(char), '08b') for char in message)
            elif mode == "hex":
                encoded_message = ' '.join(format(ord(char), '02x') for char in message)

            if encoded_message is None:
                await ctx.respond("Invalid mode selected.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to encode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid mode of {mode}")
            else:
                if hide:
                    await ctx.respond(f"Encoded message: {encoded_message}", ephemeral=True)
                    log.BOT_REPLY_SUCCESS(f"Sent encoded message to {ctx.author.name}#{ctx.author.discriminator}")
                else:
                    await ctx.respond(f"Encoded message: {encoded_message}")
                    log.BOT_REPLY_SUCCESS(f"Sent encoded message to {ctx.author.name}#{ctx.author.discriminator}")
            await command_topper(ctx)

    @bot.slash_command(name="decode", description="Decode a message")
    async def decode_command(ctx,
                            message: discord.Option(str, description="Message to decode") = None, # type: ignore
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Decode mode") = None, # type: ignore
                            key: discord.Option(str, description="Key to decode with") = None, # type: ignore
                            hide: discord.Option(bool, description="Hide the message") = False): # type: ignore
        if command_ban_check(ctx):
            return
        if ctx.guild == None and not await check_if_user_has_premium(ctx.author):
            await ctx.respond("Sorry, but this command can only be used in a server! Upgrade to Utility Belt+ to use commands in DMs and help support us.", ephemeral=True)
            log.BOT_REPLY_FAIL(f"Blocked decode command from {ctx.author.name}#{ctx.author.discriminator} due to not being in a server")
            return
        
        else:
            
            """Decode a message"""
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} message = {message} mode = {mode} key = {key} hide = {hide}")
            if message is None:
                await ctx.respond("Please enter a message to decode.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to no message")
                return
            if mode is None:
                await ctx.respond("Please enter a mode to decode with.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to no mode")
                return

            decoded_message = None

            if mode == "base64":
                try:
                    decoded_bytes = base64.b64decode(message.encode())
                    decoded_message = decoded_bytes.decode()
                except ValueError:
                    await ctx.respond("Invalid base64 encoded message.", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid base64 message")
            elif mode == "rot13":
                decoded_message = codecs.decode(message, 'rot_13')
            elif mode == "caesar":
                if key is None or not key.isdigit():
                    await ctx.respond("Please enter a valid key for the Caesar cipher.", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid key of {key}")
                    return
                decoded_message = ub.caesar_cipher_decode(message, key)
            elif mode == "vigenere":
                if key is None:
                    await ctx.respond("Please enter a valid key for the Vigenère cipher.", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid key of {key}")
                    return
                decoded_message = ub.vigenere_cipher_decode(message, key)
            elif mode == "atbash":
                decoded_message = ub.atbash_cipher_decode(message)
            elif mode == "binary":
                decoded_message = ub.binary_to_text(message)
            elif mode == "hex":
                decoded_message = ub.hex_to_text(message)

            if decoded_message is None:
                await ctx.respond("Invalid mode selected.", ephemeral=True)
                log.BOT_REPLY_FAIL(f"Failed to decode message for {ctx.author.name}#{ctx.author.discriminator} due to invalid mode of {mode}")
            else:
                if hide:
                    await ctx.respond(f"Decoded message: {decoded_message}", ephemeral=True)
                    log.BOT_REPLY_SUCCESS(f"Sent decoded message to {ctx.author.name}#{ctx.author.discriminator}")
                else:
                    await ctx.respond(f"Decoded message: {decoded_message}")
                    log.BOT_REPLY_SUCCESS(f"Sent decoded message to {ctx.author.name}#{ctx.author.discriminator}")

            await command_topper(ctx)

    @bot.slash_command(name="feedback", description="Send feedback to the developer")
    async def send_bot_owner_feedback(ctx,
        option: discord.Option(str, choices=["Bug Report", "Feature Request", "Other"], description="What are you reporting?", required=True), # type: ignore
        feature: discord.Option(str, choices=["Command", "Profile", "Other"], description="What feature is this about?", required=True), # type: ignore
        description: discord.Option(str, description="Describe the issue / change", required=True) # type: ignore
    ):
            if command_ban_check(ctx):
                return
            log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command} option = {option} feature = {feature} description = {description}")
            #make post in feedback channel in support server
            feedbackID = str(f"{ctx.author.id}{ub.get_date_time_gmt()}")
            feedbackID = int(hashlib.sha256(str(feedbackID).encode()).hexdigest(), 16) % 100001
            embed = discord.Embed(title="Bot Owner Notification", description=f"**{ctx.author.name}#{ctx.author.discriminator}** has submitted feedback", color=discord.Color.red())
            embed.add_field(name="Feedback Type", value=option, inline=False)
            embed.add_field(name="Feedback Feature", value=feature, inline=False)
            embed.add_field(name="Feedback Description", value=description, inline=False)
            embed.add_field(name="Server", value=ctx.guild, inline=False)
            embed.add_field(name="Channel", value=ctx.channel, inline=False)
            embed.add_field(name="User", value=ctx.author, inline=False)
            embed.add_field(name="Feedback ID", value=feedbackID, inline=False)
            embed.set_footer(text=f"User ID: {ctx.author.id}")
            try:
                await bot.get_channel(ub.read_toml_var("feedbackChannel")).send(embed=embed)
                log.BOT_REPLY_SUCCESS(f"Sent feedback to bot owner from {ctx.author.name}#{ctx.author.discriminator}")
            except Exception as e:
                # print(f"{e}" + " - Failed to send feedback")
                log.error(e)
                # print ("Falling back to DMs")
                botOwner = bot.get_user(ub.read_toml_var("botOwner"))  # Get the bot owner
                try:
                    await botOwner.send(embed=embed)
                    log.BOT_REPLY_SUCCESS(f"Sent feedback to bot owner from {ctx.author.name}#{ctx.author.discriminator}")
                except Exception as e:
                    # print(f"{e}" + " - Failed to send feedback")
                    log.error(e)
                    await ctx.respond(f"Sorry, feedback failed to send!", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to send feedback to bot owner from {ctx.author.name}#{ctx.author.discriminator}")
                    return
            await ctx.respond(f"Thanks, Feedback has been sent!\nTicket ID: {feedbackID}", ephemeral=True)
            log.BOT_REPLY_SUCCESS(f"Ticked ID {feedbackID}")
            await command_topper(ctx)

    @bot.slash_command(name="help", description="Get help")
    async def help_command(ctx):
        if command_ban_check(ctx):
            return
        """Get help"""
        log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
        embed = discord.Embed(title="Help", color=discord.Color.green())
        embed.add_field(name="imagine", value="AI Generate an image quickly", inline=False)
        embed.add_field(name="image-to-gif", value="Convert an image to a gif", inline=False)
        embed.add_field(name="video-to-gif", value="Convert a video to a gif", inline=False)
        embed.add_field(name="speech-bubble", value="Add a speech bubble to an image", inline=False)
        embed.add_field(name="encode", value="Encode a message", inline=False)
        embed.add_field(name="decode", value="Decode a message", inline=False)
        embed.add_field(name="timestamp", value="Convert a time to a timestamp", inline=False)
        embed.add_field(name="qr-code", value="Generate a qr code", inline=False)
        embed.add_field(name="rps", value="**BETA** Play rock paper scissors with another user", inline=False)
        embed.add_field(name="urban", value="Search urban dictionary", inline=False)
        embed.add_field(name="urban-random-word", value="Get a random word from urban dictionary", inline=False)
        embed.add_field(name="units", value="Convert units", inline=False)
        embed.add_field(name="notes", value="Read your notes", inline=False)
        embed.add_field(name="note-new", value="Write a new note", inline=False)
        embed.add_field(name="note-edit", value="Edit a note", inline=False)
        embed.add_field(name="note-delete", value="Delete a note", inline=False)
        embed.add_field(name="feedback", value="Send feedback", inline=False)
        embed.add_field(name="help", value="Get help", inline=False)
        embed.add_field(name="invite", value="Invite the bot", inline=False)
        embed.add_field(name="vote", value="Vote for the bot and claim a reward", inline=False)
        await ctx.respond(embed=embed)
        log.BOT_REPLY_SUCCESS(f"Sent help to {ctx.author.name}#{ctx.author.discriminator}")
        await command_topper(ctx)
        
    @bot.slash_command(name="vote", description="Vote for the bot and claim a reward")
    async def vote(ctx):
        if command_ban_check(ctx):
            return
        log.BOT_GOT_COMMAND(f"{ctx.author.name}#{ctx.author.discriminator} - /{ctx.command}")
        # Check if the user has voted on top.gg
        headers = {'Authorization': TOP_GG_TOKEN}
        request = requests.get(f"https://top.gg/api/bots/{TOP_GG_ID}/check?userId={ctx.author.id}", headers=headers)
        if request.status_code == 200:
            data = request.json()
            if data['voted'] == 1:
                await ctx.respond("Thanks for voting!")
                ub.edit_user_data(ctx.author, "votes", ub.get_user_data(ctx.author, "votes") + 1)
                ub.edit_user_data(ctx.author, "username", ctx.author.name + "#" + ctx.author.discriminator)
                #give VoteReward role
                try:
                    if discord.utils.get(ctx.guild.roles, name="Vote Reward") is None:
                        await ctx.guild.create_role(name="Vote Reward", color=discord.Color.nitro_pink())
                    await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name="Vote Reward"))
                    await ctx.respond("You have been given the Vote Reward role!")
                    log.BOT_REPLY_SUCCESS(f"Gave vote reward role to {ctx.author.name}#{ctx.author.discriminator}")
                except discord.Forbidden:
                    await ctx.respond("I don't have permission to give you the Vote Reward role!", ephemeral=True)
                    log.BOT_REPLY_FAIL(f"Failed to give vote reward role to {ctx.author.name}#{ctx.author.discriminator}")

            else:
                await ctx.respond(f"You haven't voted yet!\nhttps://top.gg/bot/{TOP_GG_ID}/vote")
                log.BOT_REPLY_SUCCESS(f"Sent vote link to {ctx.author.name}#{ctx.author.discriminator}")
        else:
            await ctx.respond("Error checking vote status!")
            log.BOT_REPLY_FAIL(f"Failed to check vote status for {ctx.author.name}#{ctx.author.discriminator}")
        await command_topper(ctx)


    @bot.event
    async def on_ready():
        log.info(f"Bot is now online")

    @bot.event
    async def on_message(message):
        botOwner = bot.get_user(ub.read_toml_var("botOwner"))  # Get the bot owner
        if message.guild != None: # Any message in a server
            ub.log_guild_message(message)
            #read how many messages the user has sent and add 1
            ub.edit_user_data(message.author, "messages", ub.get_user_data(message.author, "messages") + 1)
            ub.edit_user_data(message.author, "username", message.author.name + "#" + message.author.discriminator)

            #if any keyword in keywords list is in the message content
            if any(keyword in message.content.lower() for keyword in keywords):
                embed=discord.Embed(title="Message Link Detected", url=message.jump_url, color=discord.Color.blue())
                embed.add_field(name="Message", value=message.content, inline=False)
                embed.add_field(name="Server", value=message.guild, inline=False)
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

        #BOT OWNER ONLY COMMANDS
        if message.guild == None and message.author == botOwner:
            if message.content == "!guildlist":
                # print(f"{message.author} requested guilds")
                await botOwner.send("Getting guilds...\nThis may take a while.")
                guilds = await ub.get_guild_data(bot, botOwner, discord)

                # Create a text file to store guild information
                with open("guilds.txt", "w", encoding="UTF-8") as file:
                    for guild in guilds:
                        file.write(f"Guild Name: {guild[0]}\nInvite: {guild[1]}\nID: {guild[2]}\nOwner: {guild[3]}\nMembers: {guild[4]}\nOnline: {guild[5]}\n\n")

                # Send the text file
                with open("guilds.txt", "rb") as file:
                    await botOwner.send(file=discord.File(file, "guilds.txt"))

            if message.content == ("!log"):
                # print (f"{message.author} requested log")
                await botOwner.send(file=discord.File('data/app.log'))

            if message.content == ("!clearlog"):
                # print (f"{message.author} cleared log")
                with open('data/app.log', 'w') as f:
                    f.write('')
                await botOwner.send("Log cleared")
            
            if message.content == ("!usercount"):
                # print (f"{message.author} requested user count")
                await botOwner.send(f"Users: {len(bot.users)}")

            if message.content == ("!userlist"):
                # print (f"{message.author} requested user list")
                # Write all users to a CSV file
                # username, discriminator, id, account created, name of Guilds found in, id of Guilds found in, date joined Guilds found in, user description
                with open('data/users.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Username", "Discriminator", "ID", "Account Created", "Guilds", "Guild IDs", "Date Joined Guilds", "User Description"])
                    
                    # For each user, find what guilds they are in
                    for user in bot.users:
                        guilds = []
                        guild_ids = []
                        joined_dates = []
                        
                        # Iterate through guilds to find user's membership details
                        for guild in bot.guilds:
                            member = guild.get_member(user.id)
                            if member:
                                guilds.append(guild.name)
                                guild_ids.append(str(guild.id))
                                joined_dates.append(member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))  # Format the date
                                
                        # Write the user data to the CSV file
                        guilds_str = "\n".join(guilds)
                        guild_ids_str = "\n".join(guild_ids)
                        joined_dates_str = "\n".join(joined_dates)
                        writer.writerow([user.name, user.discriminator, str(user.id), str(user.created_at), guilds_str, guild_ids_str, joined_dates_str])
                
                # Send the CSV file to the bot owner
                await botOwner.send(file=discord.File('data/users.csv'))
            
            if message.content == ("!guildcount"):
                await botOwner.send(f"Guilds: {len(bot.guilds)}")
            
            if message.content == ("!userdata"):
                await botOwner.send(file=discord.File('data/users.json'))

            if message.content.startswith("!status"):
                try:
                    status = message.content.split(" ", 1)[1]
                    ub.status(status)
                    await bot.change_presence(activity=discord.Streaming(name=status))
                    await botOwner.send(f"Status set to {status}")

                except IndexError:
                    ub.status(None)
                    await bot.change_presence(activity=None)
                    await botOwner.send("Status cleared")
                    
            if message.content.startswith("!streamstatus"):
                try:
                    status = message.content.split(" ", 1)[1]
                    ub.status(status)
                    await bot.change_presence(activity=discord.Streaming(name=status))
                    await botOwner.send(f"Status set to {status}")

                except IndexError:
                    ub.status(None)
                    await bot.change_presence(activity=None)
                    await botOwner.send("Status cleared")

            if message.content == ("!guilds.zip"):
                guildsZip = ub.zip_archive_folder('guilds')
                await botOwner.send(file=discord.File(guildsZip))
                os.remove(guildsZip)

            if message.content.startswith("!notes"):
                try:
                    await botOwner.send(file=discord.File('data/notes.json'))
                except FileNotFoundError:
                    await botOwner.send("No notes file found")

            if message.content.startswith("!search"):
                try:
                    mode = message.content.split(" ")[1]
                    query = message.content.split(" ")[2]
                    ub.search(mode, query)
                    await botOwner.send(file=discord.File("temp/search.txt"))
                except IndexError:
                    await botOwner.send("No search term provided")

            if message.content.startswith("!user"):
                try:
                    user_id = message.content.split(" ")[1]
                    #if input is not an int convert username to id
                    if not user_id.isdigit():
                        log.BOT_PROCESS(f"Converting username to user ID")
                        user_id = ub.get_user_id(user_id)
                    user = bot.get_user(int(user_id))
                    embed = discord.Embed(title="User Lookup", color=discord.Color.green())
                    embed.set_thumbnail(url=user.avatar.url)
                    embed.add_field(name="Username", value=user.name, inline=True)
                    embed.add_field(name="Discriminator", value=user.discriminator, inline=True)
                    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    embed.add_field(name="Bot", value=user.bot, inline=True)
                    embed.add_field(name="Guilds", value="\n".join([guild.name for guild in bot.guilds if guild.get_member(user.id)]))
                    embed.add_field(name="Guild IDs", value="\n".join([str(guild.id) for guild in bot.guilds if guild.get_member(user.id)]))
                    embed.add_field(name="Date Joined Guilds", value="\n".join([guild.get_member(user.id).joined_at.strftime("%Y-%m-%d %H:%M:%S") for guild in bot.guilds if guild.get_member(user.id)]), inline=True)
                    
                    embed.set_footer(text=f"User ID: {user.id}")
                    await botOwner.send(embed=embed)
                except IndexError:
                    await botOwner.send("No user ID provided")
                except AttributeError:
                    await botOwner.send("User not found")

            if message.content.startswith("!guild"):
                try:
                    guild_id = message.content.split(" ")[1]
                    guild = bot.get_guild(int(guild_id))
                    embed = discord.Embed(title="Guild Lookup", color=discord.Color.green())
                    embed.add_field(name="Guild Name", value=guild.name, inline=True)
                    embed.add_field(name="Owner", value=guild.owner, inline=True)
                    embed.add_field(name="Members", value=len(guild.members), inline=True)
                    embed.add_field(name="Online", value=len([member for member in guild.members if member.status != discord.Status.offline]), inline=True)
                    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
                    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
                    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                    embed.set_thumbnail(url=guild.icon.url)
                    embed.set_footer(text=f"Guild ID: {guild.id}")
                    await botOwner.send(embed=embed)
                except IndexError:
                    await botOwner.send("No guild ID provided")
                except AttributeError as e:
                    await botOwner.send(f"Guild not found: {e}")

            if message.content.startswith("!invme"):
                try: expireTime = message.content.split(" ")[2]
                except IndexError: expireTime = 60
                invite = await ub.create_guild_invite(bot, botOwner, message.content.split(" ")[1], discord, expireTime)
                await botOwner.send(f"Invite: {invite}\nExpires after {expireTime} seconds")

            if message.content.startswith("!stats"):
                draw_users = False
                draw_guilds = False
                draw_commands = False
                draw_diff = False
                if "user" in message.content:
                    draw_users = True
                if "guild" in message.content:
                    draw_guilds = True
                if "command" in message.content:
                    draw_commands = True
                if "diff" in message.content:
                    draw_diff = True
                if "user" not in message.content and "guild" not in message.content and "command" not in message.content and "diff" not in message.content:
                    draw_users = True
                    draw_guilds = True
                    draw_commands = True
                    draw_diff = False
                if "-t " in message.content:
                    # get everything after -t 
                    time = message.content.split("-t ")[1]
                else:
                    time = None

                plot = ub.gen_csv_plot("data/data.csv", draw_users, draw_guilds, draw_commands, draw_diff, time)
                #send data/data.csv
                if "file" in message.content:
                    await botOwner.send(file=discord.File('data/data.csv'))
                await botOwner.send(file=discord.File(plot))

            if message.content.startswith("!ban"):
                try:
                    user_id = message.content.split(" ")[1]
                    if not user_id.isdigit():
                        log.BOT_PROCESS(f"Converting username to user ID")
                        user_id = ub.get_user_id(user_id)
                    user = bot.get_user(int(user_id))

                    # append user to banned_users.json if not already banned
                    try:
                        with open('config/banned_users.json', 'r') as f:
                            banned_users = json.load(f)
                    except FileNotFoundError:
                        banned_users = []

                    if user.id not in banned_users:
                        banned_users.append(user.id)
                        with open('config/banned_users.json', 'w') as f:
                            json.dump(banned_users, f)
                        await botOwner.send(f"Banned {user.name}#{user.discriminator}")
                    else:
                        await botOwner.send(f"{user.name}#{user.discriminator} is already banned")
                except IndexError:
                    await botOwner.send("No user ID provided")

            if message.content.startswith("!unban"):
                try:
                    user_id = message.content.split(" ")[1]
                    if not user_id.isdigit():
                        log.BOT_PROCESS(f"Converting username to user ID")
                        user_id = ub.get_user_id(user_id)
                    user = bot.get_user(int(user_id))

                    # remove user from banned_users.json
                    try:
                        with open('config/banned_users.json', 'r') as f:
                            banned_users = json.load(f)
                    except FileNotFoundError:
                        banned_users = []
                    banned_users.remove(user.id)
                    with open('config/banned_users.json', 'w') as f:
                        json.dump(banned_users, f)

                    await botOwner.send(f"Unbanned {user.name}#{user.discriminator}")
                except IndexError:
                    await botOwner.send("No user ID provided")

            if message.content.startswith("!dm"):
                try:
                    user_id = message.content.split(" ")[1]
                    if not user_id.isdigit():
                        log.BOT_PROCESS(f"Converting username to user ID")
                        user_id = ub.get_user_id(user_id)
                    user = bot.get_user(int(user_id))
                    dm_message = message.content.split(" ", 2)[2]
                    await user.send(dm_message)
                    await botOwner.send(f"Sent message to {user.name}#{user.discriminator}")
                except IndexError:
                    await botOwner.send("No user ID provided")

            if message.content.startswith("!help"):
                # https://cdn.discordapp.com/emojis/1191381954453586061.gif?size=96&quality=lossless
                # https://discord.com/channels/1170496731872493739/1178817154620067851/1191382117972717649
                await botOwner.send(f"""**!help** - Send this message
**!guildlist** - Send a list of guilds the bot is in
**!log** - Send the log file
**!clearlog** - Clear the log file
**!usercount** - Send the number of users the bot can see
**!userlist** - Send a CSV file of all users the bot can see
**!guildcount** - Send the number of guilds the bot is in
**!userdata** - Send the data/users.json file
**!status** - Set the bot status
**!streamstatus** - Set the bot stream status
**!ban** - Ban a user from using the bot
**!unban** - Unban a user from using the bot
**!guilds.zip** - Send a zip file of all guilds the bot is in
**!notes** - Send the data/notes.json file
**!search** - Search all messages for a query
**!user** - Search a user ID
**!guild** - Search a guild ID
**!invme** - Create a guild invite
**!stats** - Send the data/data.csv file
**!dm** - Message a user by ID
                                                    """)

            if message.content.startswith("!sku"):
                await botOwner.send(await check_if_user_has_premium(message.author))

    bot.response_messages = {}
    bot.run(BOT_TOKEN)

if __name__ == "__main__":        
    main()