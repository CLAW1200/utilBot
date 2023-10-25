

"""

RPS is bugged, expire timer not keeping accurate time, message is edited even when game is over

"""
from discord.ui import View, Button
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
import asyncio
import traceback
ureg = UnitRegistry()

#utilityBot.update_version()

keywords = {
    "https://discord",
    "claw",
}

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
        if ctx.guild == None:
            return True

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
        utilityBot.edit_user_data(ctx.author, "username", ctx.author.name + "#" + ctx.author.discriminator)
        if utilityBot.get_user_data(ctx.author, "commandsUsed") <= 1:
            await ctx.respond(f"Welcome to Utility Belt! You can use **/help** to get a list of commands.\nPlease use **/feedback** if you have any issues!\nRemember to use **/vote** if you find me useful :) - This will be the only reminder", ephemeral=True)

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
            utilityBot.archive_file(newGif)
            log.info(f"Converted image {image_link}")
        except Image.UnidentifiedImageError:
            await ctx.edit(content = f"Sorry, but that image link is invalid!")
        await command_topper(ctx)
        utilityBot.logging_command(ctx, image_link)

    @bot.slash_command(name="video-to-gif", description="Take a video link and send it as a gif")
    async def video_to_gif_command(
        ctx: discord.ApplicationContext,
        video_link: str,
        fps: discord.Option(int, "The FPS of the gif", required=False, default=25),
        scale: discord.Option(int, "The scale of the gif", required=False),
    ):
        #do not download videos larger than maxFileSize
        if utilityBot.get_file_size(video_link) > utilityBot.read_toml_var("maxFileSize"):
            await ctx.respond(f"Sorry, but the max video size is {utilityBot.read_toml_var('maxFileSize')/1000000}MB!", ephemeral=True)
            return
        if fps > 40:
            await ctx.respond(f"Sorry, but the max FPS is 40!", ephemeral=True)
            return
        if scale != None:
            if scale > 500:
                await ctx.respond(f"Sorry, but the max scale is 500px!", ephemeral=True)
                return
        
        await ctx.respond(f"Converting video to gif... ")
        try:
            newGif = utilityBot.convert_video_to_gif(video_link, fps, scale)
            await ctx.edit(content = f"Here is your gif!" , file=discord.File(newGif))
            utilityBot.archive_file(newGif)
            log.info(f"Converted image {video_link}")
        except Exception as e:
            await ctx.edit(content = f"Sorry, but that video link is invalid!")
            print (e)
            traceback.print_exc()
        await command_topper(ctx)
        utilityBot.logging_command(ctx, video_link, fps, scale)

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
        except Exception as e:
            await ctx.edit(content = f"Sorry, but I could not add a speech bubble to that image!")
            log.error(e)
        try:
            utilityBot.archive_file(newImage)
        except Exception as e:
            print(f"{e}" + " - Failed to remove image")
            log.error(e)
        await command_topper(ctx)
        utilityBot.logging_command(ctx, image_link, speech_bubble_size)

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
        await command_topper(ctx)
        utilityBot.logging_command(ctx)


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
        utilityBot.archive_file(newImage)
        log.info(f"Added impact font to image {image_link}")
        await command_topper(ctx)
        utilityBot.logging_command(ctx, image_link, top_text, bottom_text, font_size, font_color)

    @bot.slash_command(name="invite", description="Get the bot's invite link")
    async def invite_command(ctx):
        #respond with message with button that links to bot invite link
        client_id = bot.user.id
        inviteLink = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={utilityBot.read_toml_var('permissionsInt')}"
        await ctx.respond(f"{inviteLink}", ephemeral=True)
        await command_topper(ctx)
        utilityBot.logging_command(ctx)

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
        utilityBot.logging_command(ctx, word, random_result)

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
        utilityBot.logging_command(ctx, word)

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
        utilityBot.logging_command(ctx, value, unit_from, unit_to)

    @bot.slash_command(name="note-new", description="Write a new note")
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

        await ctx.respond("New note added!\nSee your new note with /notes.", ephemeral=True)
        await command_topper(ctx)
        utilityBot.logging_command(ctx, note)

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

        if user_notes:
            undeleted_user_notes = [n for n in user_notes if "[X]" not in n]

            if 1 <= index <= len(undeleted_user_notes):
                undeleted_index = index - 1
                edited_note = undeleted_user_notes[undeleted_index]
                user_notes[user_notes.index(edited_note)] = note
                notes[str(ctx.author.id)] = user_notes

                with open("notes.json", "w") as f:
                    json.dump(notes, f, indent=4)

                await ctx.respond(f"Note {index} updated!", ephemeral=True)
            else:
                await ctx.respond("Invalid note index!", ephemeral=True)
        else:
            await ctx.respond("You have no notes!", ephemeral=True)
        await command_topper(ctx)
        utilityBot.logging_command(ctx, index, note)

    @bot.slash_command(name="notes", description="Read your notes")
    async def my_notes_command(ctx):
        """Read the user's notes"""
        notes = {}
        try:
            with open("notes.json", "r") as f:
                notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        user_notes = notes.get(str(ctx.author.id), [])

        non_completed_notes = [note for note in user_notes if "[X]" not in note]

        if non_completed_notes:
            formatted_notes = '\n'.join(f"{i+1}. {note}" for i, note in enumerate(non_completed_notes))
            await ctx.respond(f"Your notes:\n{formatted_notes}", ephemeral=True)
        else:
            await ctx.respond("You have no notes!", ephemeral=True)
        await command_topper(ctx)
        utilityBot.logging_command(ctx)


    @bot.slash_command(name="note-delete", description="Delete a note or leave index blank to delete all")
    #delete all or delete one
    async def delete_note_command(ctx, index: int = None):
        """Delete a note, or all for the user"""
        notes = {}

        try:
            with open("notes.json", "r") as f:
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
                    return
                user_notes[user_notes.index(deleted_note)] = f"[X] {deleted_note}"
                notes[str(ctx.author.id)] = user_notes
                await ctx.respond(f"Note {index} deleted!", ephemeral=True)
            else:
                await ctx.respond("Invalid note index!", ephemeral=True)

            with open("notes.json", "w") as f:
                json.dump(notes, f, indent=4)
        else:
            await ctx.respond("You have no notes!", ephemeral=True)
        await command_topper(ctx)
        utilityBot.logging_command(ctx, index)



    @bot.slash_command(name="cat", description="Get a random cat picture")
    async def cat_command(ctx):
        """Get a random cat gif"""
        #use gif search function
        await ctx.respond(utilityBot.gif_search("silly cat"))
        await command_topper(ctx)
        utilityBot.logging_command(ctx)

    @bot.slash_command(name="find-a-friend", description="Get a random discord user")
    async def dox_command(ctx):
        def get_random_user():
            randomUser = bot.users[random.randint(0, len(bot.users))-1]
            if randomUser == ctx.author or randomUser.bot:
                return get_random_user()
            else:
                return randomUser
        await ctx.respond(f"Your new friend is {get_random_user()}!")
        await command_topper(ctx)
        utilityBot.logging_command(ctx)

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
        await command_topper(ctx)
        utilityBot.logging_command(ctx)
    
    ongoing_games = {}

    @bot.slash_command(
        name="rps",
        description="Play rock paper scissors with another user"
    )
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

        if ctx.author.id in ongoing_games or user.id in ongoing_games:
            await ctx.respond("There is already an ongoing game involving one of the players.", ephemeral=True)
            return

        view = RPSView(ctx.author, user)
        await ctx.respond(f"{user.mention} has been challenged to a game of rock paper scissors by {ctx.author.mention}!\nBoth players, please select your move.", view=view)

        ongoing_games[(ctx.author.id, user.id)] = view

    class RPSView(View):
        def __init__(self, challenger, opponent):
            super().__init__(timeout=None)  # Explicitly call the parent class's __init__
            self.challenger = challenger
            self.opponent = opponent
            self.move = None
            self.opponent_move = None
            self.timer = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user in [self.challenger, self.opponent]

        async def start_timer(self):
            await asyncio.sleep(60)  # Wait for 60 seconds

            if self.move is None or self.opponent_move is None:
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

            # Stop the timer since the game has concluded
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None  # Reset the timer

            # Compare the moves and determine the winner
            winner = determine_winner(self.move, self.opponent_move)

            # Prepare the result message mentioning the winner and the choices
            if winner == "tie":
                result_message = f"⛔ It's a tie!\n\n{self.challenger.mention} chose {self.move}.\n{self.opponent.mention} chose {self.opponent_move}."
            else:
                winner = self.challenger if winner == self.move else self.opponent
                result_message = f"🎉 {winner.mention} wins!\n\n{self.challenger.mention} chose {self.move}.\n{self.opponent.mention} chose {self.opponent_move}."

            # Edit the message with the result
            await self.message.edit(content=result_message, view=None)

            # Remove the game from the ongoing games
            del ongoing_games[self.challenger.id]
            del ongoing_games[self.opponent.id]

        async def on_timeout(self):
            # Reset the moves
            self.move = None
            self.opponent_move = None

            #if game is not over, edit message to say game is over
            if self.timer is not None:
                # Edit the message to reflect the expiration
                expiration_message = f"⌛ The game between {self.challenger.mention} and {self.opponent.mention} has expired."
                await self.message.edit(content=expiration_message, view=None)

            # Remove the game from the ongoing games
            del ongoing_games[self.challenger.id]
            del ongoing_games[self.opponent.id]

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            # Only allow the two players to interact with the buttons
            return interaction.user in [self.challenger, self.opponent]

        async def on_error(self, error, item, traceback):
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
                            message: discord.Option(str, description="Message to encode") = None,
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Encode mode") = None,
                            key: discord.Option(str, description="Key to encode with") = None,
                            hide: discord.Option(bool, description="Hide the message") = False):

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
            if key is None or not key.isdigit():
                await ctx.respond("Please enter a valid key for the Caesar cipher.", ephemeral=True)
                return
            encoded_message = utilityBot.caesar_cipher_encode(message, key)
        elif mode == "vigenere":
            if key is None:
                await ctx.respond("Please enter a valid key for the Vigenère cipher.", ephemeral=True)
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
                await ctx.respond(f"Encoded message: {encoded_message}", ephemeral=True)
            else:
                await ctx.respond(f"Encoded message: {encoded_message}")
        await command_topper(ctx)
        utilityBot.logging_command(ctx, "encode", message, mode, hide, key)

    @bot.slash_command(name="decode", description="Decode a message")
    async def decode_command(ctx,
                            message: discord.Option(str, description="Message to decode") = None,
                            mode: discord.Option(str, choices=["base64", "rot13", "caesar", "vigenere", "atbash", "binary", "hex"], description="Decode mode") = None,
                            key: discord.Option(str, description="Key to decode with") = None,
                            hide: discord.Option(bool, description="Hide the message") = False):
        
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
            if key is None or not key.isdigit():
                await ctx.respond("Please enter a valid key for the Caesar cipher.", ephemeral=True)
                return
            decoded_message = utilityBot.caesar_cipher_decode(message, key)
        elif mode == "vigenere":
            if key is None:
                await ctx.respond("Please enter a valid key for the Vigenère cipher.", ephemeral=True)
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
                await ctx.respond(f"Decoded message: {decoded_message}", ephemeral=True)
            else:
                await ctx.respond(f"Decoded message: {decoded_message}")

        utilityBot.logging_command(ctx, "decode", message, mode, hide, key)


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
            await command_topper(ctx)
            utilityBot.logging_command(ctx, "feedback", feedback_type, feedback_feature, feedback_description)

    @bot.slash_command(name="help", description="Get help")
    async def help_command(ctx):
        """Get help"""
        embed = discord.Embed(title="Help", color=discord.Color.green())
        embed.add_field(name="image-to-gif", value="Convert an image to a gif", inline=False)
        embed.add_field(name="video-to-gif", value="Convert a video to a gif", inline=False)
        embed.add_field(name="speech-bubble", value="Add a speech bubble to an image", inline=False)
        embed.add_field(name="encode", value="Encode a message", inline=False)
        embed.add_field(name="decode", value="Decode a message", inline=False)
        embed.add_field(name="rps", value="Play rock paper scissors with another user", inline=False)
        embed.add_field(name="cat" , value="Get a random cat gif", inline=False)
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
        utilityBot.logging_command(ctx)


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
                utilityBot.edit_user_data(ctx.author, "username", ctx.author.name + "#" + ctx.author.discriminator)
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
        utilityBot.logging_command(ctx)

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
            utilityBot.log_guild_message(message)
            #read how many messages the user has sent and add 1
            utilityBot.edit_user_data(message.author, "messages", utilityBot.get_user_data(message.author, "messages") + 1)
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

        #BOT OWNER ONLY COMMANDS
        if message.guild == None and message.author == botOwner:
            if message.content == "!guilds":
                print(f"{message.author} requested guilds")
                guilds = await utilityBot.get_guild_invite(bot)

                # Create a text file to store guild information
                with open("guilds.txt", "w", encoding="UTF-8") as file:
                    for guild in guilds:
                        file.write(f"Guild Name: {guild[0]}\nInvite: {guild[1]}\nID: {guild[2]}\nOwner: {guild[3]}\nMembers: {guild[4]}\nOnline: {guild[5]}\n\n")

                # Send the text file
                with open("guilds.txt", "rb") as file:
                    await botOwner.send(file=discord.File(file, "guilds.txt"))

                # Delete the temporary file
                utilityBot.archive_file("guilds.txt")


            if message.content == ("!log"):
                print (f"{message.author} requested log")
                await botOwner.send(file=discord.File('app.log'))

            if message.content == ("!clearlog"):
                print (f"{message.author} cleared log")
                with open('app.log', 'w') as f:
                    f.write('')
                await botOwner.send("Log cleared")
            
            if message.content == ("!usercount"):
                print (f"{message.author} requested user count")
                await botOwner.send(f"Users: {len(bot.users)}")

            if message.content == ("!userlist"):
                print (f"{message.author} requested user list")
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
            
            if message.content == ("!guildcount"):
                print (f"{message.author} requested guild count")
                await botOwner.send(f"Guilds: {len(bot.guilds)}")
            
            if message.content == ("!userdata"):
                print (f"{message.author} requested users.json")
                await botOwner.send(file=discord.File('users.json'))

            if message.content.startswith("!status"):
                print (f"{message.author} requested status change")

                try:
                    status = message.content.split(" ")[1]
                    utilityBot.status(status)
                    await bot.change_presence(activity=discord.Game(name=status))
                    await botOwner.send(f"Status set to {status}")

                except IndexError:
                    utilityBot.status(None)
                    await bot.change_presence(activity=None)
                    await botOwner.send("Status cleared")

            if message.content == ("!guilds.zip"):
                print (f"{message.author} requested guilds.zip")
                shutil.make_archive('guilds', 'zip', 'guilds')
                await botOwner.send(file=discord.File('guilds.zip'))
                utilityBot.archive_file('guilds.zip')

            if message.content.startswith("!notes"):
                print (f"{message.author} requested notes")
                try:
                    await botOwner.send(file=discord.File('notes.json'))
                except FileNotFoundError:
                    await botOwner.send("No notes file found")

            if message.content.startswith("!search"):
                print (f"{message.author} requested search")
                try:
                    mode = message.content.split(" ")[1]
                    query = message.content.split(" ")[2]
                    print (f"Mode: {mode}, Query: {query}")
                    utilityBot.search(mode, query)
                    await botOwner.send(file=discord.File("temp/search.txt"))
                    utilityBot.archive_file("temp/search.txt")
                except IndexError:
                    await botOwner.send("No search term provided")

            if message.content.startswith("!userlookup"):
                print (f"{message.author} requested user lookup")
                try:

                    user_id = message.content.split(" ")[1]
                    user = bot.get_user(int(user_id))
                    embed = discord.Embed(title="User Lookup", color=discord.Color.green())
                    embed.set_thumbnail(url=user.avatar.url)
                    embed.add_field(name="Username", value=user.name, inline=True)
                    embed.add_field(name="Discriminator", value=user.discriminator, inline=True)
                    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    embed.add_field(name="Bot", value=user.bot, inline=True)
                    #embed.add_field(name="Status", value=user.status, inline=True)
                    embed.add_field(name="Guilds", value="\n".join([guild.name for guild in bot.guilds if guild.get_member(user.id)]))
                    embed.add_field(name="Guild IDs", value="\n".join([str(guild.id) for guild in bot.guilds if guild.get_member(user.id)]))
                    embed.add_field(name="Date Joined Guilds", value="\n".join([guild.get_member(user.id).joined_at.strftime("%Y-%m-%d %H:%M:%S") for guild in bot.guilds if guild.get_member(user.id)]), inline=True)
                    
                    embed.set_footer(text=f"User ID: {user.id}")
                    await botOwner.send(embed=embed)
                except IndexError:
                    await botOwner.send("No user ID provided")
                except AttributeError:
                    await botOwner.send("User not found")

            if message.content.startswith("!guildlookup"):
                print (f"{message.author} requested guild lookup")
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
        
            if message.content.startswith("!help"):
                print (f"{message.author} requested help")
                await botOwner.send("""**!help** - Send this message
**!guilds** - Send a list of guilds the bot is in
**!log** - Send the log file
**!clearlog** - Clear the log file
**!usercount** - Send the number of users the bot can see
**!userlist** - Send a CSV file of all users the bot can see
**!guildcount** - Send the number of guilds the bot is in
**!userdata** - Send the users.json file
**!status** - Set the bot status
**!guilds.zip** - Send a zip file of all guilds the bot is in
**!notes** - Send the notes.json file
**!search** - Search all messages for a query
**!userlookup** - Search a user ID
**!guildlookup** - Search a guild ID                        
                """)

    bot.response_messages = {}
    bot.run(TOKEN)

if __name__ == "__main__":
    main()