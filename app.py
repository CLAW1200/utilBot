from discord.ui import View
import os
import random
import logging as log
import discord
import toml
import shutil
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
import utilityBot
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

def logging_message(message):
    # Get the server name and channel name
    server_name = message.guild.name
    channel_name = message.channel.name
    
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
        file.write(f"Message: {message.content}\n")
        file.write(f"{attachments_info}\n")
        file.write(f"{embeds_info}\n")
        file.write("--------------------------------\n")

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
    GIPHY_API_KEY = data["giphy-api-key"]
    log.debug(f"Token read from '{tokenFile}'")

#if there is no temp folder make one
if not os.path.exists("temp"):
    os.makedirs("temp")



def main():
    log.debug("Starting Main()")
    bot = discord.Bot(intents=discord.Intents.all())
    log.debug("Bot object created")

    def check_bot_permissions(ctx):
        binary_guild_permissions = bin(ctx.guild.me.guild_permissions.value)
        binary_required_permissions = bin(utilityBot.read_toml_var("permissionsInt"))

        #perform binary AND operation on the two binary strings
        check = int(binary_guild_permissions, 2) & int(binary_required_permissions, 2)
        if check == int(binary_required_permissions, 2):
            return True
        else:
            return False
    
    async def command_topper(ctx):
        utilityBot.edit_user_data(ctx.author, "commandsUsed", utilityBot.get_user_data(ctx.author, "commandsUsed") + 1)
        if utilityBot.get_user_data(ctx.author, "commandsUsed") <= 1:
            await ctx.respond(f"Welcome to Utility Belt! You can use **/help** to get a list of commands.\nRemember to use **/vote** if you find me useful (This will be the only reminder)", ephemeral=True)

        if not check_bot_permissions(ctx):
            await ctx.respond("Warning: I am missing some permissions which may cause errors. Please use /update-permissions to avoid any problems using commands", ephemeral=True)
            return False
        return True

    @bot.slash_command(name="image-to-gif", description="Take an image link and send it as a gif")
    async def image_to_gif_command(ctx: discord.ApplicationContext, image_link: str):
        if utilityBot.get_file_size(image_link) > utilityBot.read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {utilityBot.read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        await ctx.respond(f"Converting image to gif... ") # this message will be deleted when the gif is sent
        try:
            newGif = utilityBot.convert_image_to_gif(image_link)
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
        if utilityBot.get_file_size(video_link) > utilityBot.read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {utilityBot.read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        
        if fps > 25:
            await ctx.respond(f"Sorry, but the max FPS is 25!", ephemeral=True)
            return
        
        if scale > 500:
            await ctx.respond(f"Sorry, but the max scale is 500px!", ephemeral=True)
            return
        
        await ctx.respond(f"Converting video to gif... ")
        try:
            newGif = utilityBot.convert_video_to_gif(video_link, fps, scale)
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
        if utilityBot.get_file_size(image_link) > utilityBot.read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {utilityBot.read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        
        if speech_bubble_size > 1 or speech_bubble_size < 0:
            await ctx.respond(f"Sorry, values between 0 and 1 only!", ephemeral=True)
            return
        await ctx.respond(f"Adding speech bubble to image... ")
        try:
            newImage = utilityBot.add_speech_bubble(image_link, speech_bubble_size)
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
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={utilityBot.read_toml_var('permissionsInt')}"
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

        newImage = utilityBot.add_impact_font(image_link, top_text, bottom_text, font_size, font_color)
        await ctx.edit(content = (f"Here is your image!") , file=discord.File(newImage))
        os.remove(newImage)
        log.info(f"Added impact font to image {image_link}")
        await command_topper(ctx)
        logging_command(ctx, image_link, top_text, bottom_text, font_size, font_color)

    @bot.slash_command(name="invite", description="Get the bot's invite link")
    async def invite_command(ctx):
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={utilityBot.read_toml_var('permissionsInt')}"
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


    @bot.slash_command(name="cat", description="Get a random cat picture")
    async def cat_command(ctx):
        """Get a random cat gif"""
        #use gif search function
        await ctx.respond(utilityBot.gif_search("silly cat"))

    @bot.slash_command(name="find-a-friend", description="Get a random discord user")
    async def dox_command(ctx):
        def get_random_user():
            randomUser = bot.users[random.randint(0, len(bot.users))-1]
            if randomUser == ctx.author or randomUser.bot:
                return get_random_user()
            else:
                return randomUser
        await ctx.respond(f"Your new friend is {get_random_user()}!")

    @bot.slash_command(name="peepee", description="Get your peepee size")
    async def peepee_command(ctx, user: discord.Option(discord.User, description="User to get peepee size of") = None):
        """Get your peepee size"""
        #hash the user id to get a random number
        if user == None:
            user = ctx.author
        peepeeSize = int(hashlib.sha256(str(user.id).encode()).hexdigest(), 16) % 10
        if user.id == utilityBot.read_toml_var("botOwner"):
            peepeeSize = 34
        peepee = "8" + "=" * peepeeSize + "D"
        await ctx.respond(f"{user.mention} peepee size is {peepee}")

    @bot.slash_command(name="rps", description="Play rock paper scissors with another user")
    async def rps_command(ctx, user: discord.Option(discord.User, description="User to play with") = None):
        """Play rock paper scissors with another user"""
        if user is None:
            await ctx.respond("Please mention a user to play with.", ephemeral=True)
            return
        
        if user == ctx.author:
            await ctx.respond("Sorry, you can't play with yourself ;)", ephemeral=True)
            return
        
        if user.bot:
            await ctx.respond("You can't play with a bot!", ephemeral=True)
            return

        view = RPSView(ctx.author, user)
        await ctx.respond(f"{user.mention} has been challenged to a game of rock paper scissors by {ctx.author.mention}!\nBoth players, please select your move.", view=view)

    class RPSView(View):
        def __init__(self, challenger, opponent):
            super().__init__()
            self.challenger = challenger
            self.opponent = opponent
            self.move = None
            self.opponent_move = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            # Only allow the two players to interact with the buttons
            return interaction.user in [self.challenger, self.opponent]

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

            if interaction.user == self.challenger and self.move is None:
                self.move = move
            elif interaction.user == self.opponent and self.opponent_move is None:
                self.opponent_move = move
            else:
                return

            await self.send_results(interaction)

        async def send_results(self, interaction):
            if self.opponent_move is None or self.move is None:
                return

            # Compare the moves and determine the winner
            winner = determine_winner(self.move, self.opponent_move)

            # Prepare the result message mentioning the winner and the choices
            if winner == "tie":
                result_message = f"⛔ It's a tie!\n\n{self.challenger.mention} chose {self.move}.\n{self.opponent.mention} chose {self.opponent_move}."
            else:
                winner = self.challenger if winner == self.move else self.opponent
                result_message = f"🎉 {winner.mention} wins!\n\n{self.challenger.mention} chose {self.move}.\n{self.opponent.mention} chose {self.opponent_move}."

            await interaction.followup.send(result_message)

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
                            message: discord.Option(str, description="Message to encode") = None,
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Encode mode") = None,
                            hide: discord.Option(bool, description="Hide the message") = False,
                            key: discord.Option(str, description="Key to encode with") = None):
        """Encode a message"""
        if message is None:
            await ctx.respond("Please enter a message to encode.", ephemeral=True)
            return
        if mode is None:
            await ctx.respond("Please enter a mode to encode with.", ephemeral=True)
            return

        encoded_message = None

        if mode == "base64":
            encoded_message = base64.b64encode(message.encode()).decode()
        elif mode == "rot13":
            encoded_message = codecs.encode(message, 'rot_13')
        elif mode == "caesar":
            if key is None:
                await ctx.respond("Please enter a key for the Caesar cipher.", ephemeral=True)
                return
            encoded_message = utilityBot.caesar_cipher_encode(message, key)
        elif mode == "vigenere":
            if key is None:
                await ctx.respond("Please enter a key for the Vigenère cipher.", ephemeral=True)
                return
            encoded_message = utilityBot.vigenere_cipher_encode(message, key)
        elif mode == "atbash":
            encoded_message = utilityBot.atbash_cipher_encode(message)
        elif mode == "binary":
            encoded_message = ' '.join(format(ord(char), '08b') for char in message)
        elif mode == "hex":
            encoded_message = ' '.join(format(ord(char), '02x') for char in message)

        if encoded_message is None:
            await ctx.respond("Invalid mode selected.", ephemeral=True)
        else:
            if hide:
                # Hide the message if hide option is enabled
                encoded_message = "*" * len(encoded_message)
            await ctx.respond(f"Encoded message: {encoded_message}")

    @bot.slash_command(name="decode", description="Decode a message")
    async def decode_command(ctx,
                            message: discord.Option(str, description="Message to decode") = None,
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Decode mode") = None,
                            hide: discord.Option(bool, description="Hide the message") = False,
                            key: discord.Option(str, description="Key to decode with") = None):
        """Decode a message"""
        if message is None:
            await ctx.respond("Please enter a message to decode.", ephemeral=True)
            return
        if mode is None:
            await ctx.respond("Please enter a mode to decode with.", ephemeral=True)
            return

        decoded_message = None

        if mode == "base64":
            try:
                decoded_bytes = base64.b64decode(message.encode())
                decoded_message = decoded_bytes.decode()
            except ValueError:
                await ctx.respond("Invalid base64 encoded message.", ephemeral=True)
        elif mode == "rot13":
            decoded_message = codecs.decode(message, 'rot_13')
        elif mode == "caesar":
            if key is None:
                await ctx.respond("Please enter a key for the Caesar cipher.", ephemeral=True)
                return
            decoded_message = utilityBot.caesar_cipher_decode(message, key)
        elif mode == "vigenere":
            if key is None:
                await ctx.respond("Please enter a key for the Vigenère cipher.", ephemeral=True)
                return
            decoded_message = utilityBot.vigenere_cipher_decode(message, key)
        elif mode == "atbash":
            decoded_message = utilityBot.atbash_cipher_decode(message)
        elif mode == "binary":
            decoded_message = utilityBot.binary_to_text(message)
        elif mode == "hex":
            decoded_message = utilityBot.hex_to_text(message)

        if decoded_message is None:
            await ctx.respond("Invalid mode selected.", ephemeral=True)
        else:
            if hide:
                # Hide the message if hide option is enabled
                decoded_message = "*" * len(decoded_message)
            await ctx.respond(f"Decoded message: {decoded_message}")


            
    @bot.slash_command(name="feedback", description="Send feedback")
    #feedback_type options: bug, feature, other
    #feedback_feature options: commands, events, other
    
    async def send_bot_owner_feedback(ctx,
        feedback_type: discord.Option(str, choices=["Bug Report", "Feature Request", "Other"], description="What are you reporting?") = None,
        feedback_feature: discord.Option(str, choices=["Command", "Profile", "Other"], description="What feature is this about?") = None,
        feedback_description: discord.Option(str, description="Describe the issue / change") = None
    ):
            botOwner = bot.get_user(utilityBot.read_toml_var("botOwner"))
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
                utilityBot.edit_user_data(ctx.author, "votes", utilityBot.get_user_data(ctx.author, "votes") + 1)
                #give VoteReward role
                try:
                    if discord.utils.get(ctx.guild.roles, name="Vote Reward") is None:
                        await ctx.guild.create_role(name="Vote Reward", color=discord.Color.nitro_pink())
                    await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name="Vote Reward"))
                    await ctx.respond("You have been given the Vote Reward role!")
                except discord.Forbidden:
                    await ctx.respond("I don't have permission to give you the Vote Reward role!", ephemeral=True)

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
        botOwner = bot.get_user(utilityBot.read_toml_var("botOwner"))  # Get the bot owner
        #messageAuthor = message.author.id # Get the author of the message
        #messageAuthor = bot.get_user(messageAuthor) # Get the specific author
        if message.guild != None: # Any message in a server
            logging_message(message)
            #read how many messages the user has sent and add 1
            utilityBot.edit_user_data(message.author, "messages", utilityBot.get_user_data(message.author, "messages") + 1)
            #add their username and discriminator
            utilityBot.edit_user_data(message.author, "username", message.author.name + "#" + message.author.discriminator)

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

        # (!invites secret command)
        if message.guild == None:
            if message.author == botOwner and message.content == ("!guilds"):
                guilds = await utilityBot.get_guild_invite(bot)
                guildNames = guilds[0]
                guildInvites = guilds[1]
                guildInfo = guilds[2]
                embed=discord.Embed(title="Guild Invites", color=discord.Color.green())
                #add a column for guild name and guild invite and guild info
                for i in range(len(guildNames)):
                    embed.add_field(name=guildNames[i], value=f"Invite: {guildInvites[i]}\n{guildInfo[i]}", inline=False)
                await botOwner.send(embed=embed)

            if message.author == botOwner and message.content == ("!log"):
                await botOwner.send(file=discord.File('app.log'))
            
            if message.author == botOwner and message.content == ("!clearlog"):
                with open('app.log', 'w') as f:
                    f.write('')
            
            if message.author == botOwner and message.content == ("!usercount"):
                await botOwner.send(f"Users: {len(bot.users)}")

            if message.author == botOwner and message.content == ("!userlist"):
                # Write all users to a CSV file
                # username, discriminator, id, account created, name of Guilds found in, id of Guilds found in, date joined Guilds found in, user description
                with open('users.csv', 'w', newline='', encoding='utf-8') as csvfile:
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
                await botOwner.send(file=discord.File('users.csv'))
            
            if message.author == botOwner and message.content == ("!guildcount"):
                await botOwner.send(f"Guilds: {len(bot.guilds)}")
            
            if message.author == botOwner and message.content == ("!users.json"):
                await botOwner.send(file=discord.File('users.json'))

            if message.author == botOwner and message.content.startswith("!loglevel"):
                logLevel = message.content.split(": ")[1]
                if logLevel == "debug":
                    log.setLevel(log.DEBUG)
                elif logLevel == "info":
                    log.setLevel(log.INFO)
                elif logLevel == "warning":
                    log.setLevel(log.WARNING)
                elif logLevel == "error":
                    log.setLevel(log.ERROR)
                elif logLevel == "critical":
                    log.setLevel(log.CRITICAL)
                else:
                    await botOwner.send("Invalid log level")
                await botOwner.send(f"Log level set to {logLevel}")

            if message.author == botOwner and message.content.startswith("!setstatus"):
                status = message.content.split(": ")[1]
                await bot.change_presence(activity=discord.Game(name=status))
                await botOwner.send(f"Status set to {status}")

            if message.author == botOwner and message.content == ("!clearstatus"):
                await bot.change_presence(activity=None)
                await botOwner.send("Status cleared")
            
            if message.author == botOwner and message.content == ("!guilds.zip"):
                shutil.make_archive('guilds', 'zip', 'guilds')
                await botOwner.send(file=discord.File('guilds.zip'))
                os.remove('guilds.zip')

            if message.author == botOwner and message.content.startswith("!notes"):
                await botOwner.send(file=discord.File('notes.json'))

            if message.author == botOwner and message.content.startswith("!help"):
                await botOwner.send("""\n
                **!help** - Send this message\n
                **!guilds** - List all guilds and their invites\n
                **!guilds.zip** - Send a ZIP file of all messages\n
                **!log** - Send the log file\n
                **!clearlog** - Clear the log file\n
                **!usercount** - Send the number of users\n
                **!userlist** - Send a CSV file of all users\n
                **!guildcount** - Send the number of guilds\n
                **!users.json** - Send a JSON file of all users\n
                **!loglevel** - Set the log level\n
                **!setstatus** - Set the status\n
                **!clearstatus** - Clear the status\n
                **!setcustom** - Set the custom activity\n
                """)


    bot.run(TOKEN)

if __name__ == "__main__":
    main()