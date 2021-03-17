#Dependencies___________________________________________________________________
import discord
import os
import json
import parser
import math
import requests
from pathlib import Path
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

client = commands.Bot(command_prefix = '.')
helpInfo = open('help.txt', 'r').readlines()

#Classes________________________________________________________________________
class Character:
    name = "John Doe"
    xp = 0
    focuses = {}
    image = None

    def Builder(data):
        char = Character()
        char.name = data.get('name')
        char.xp = data.get('xp')
        char.focuses = data.get('focuses')
        char.image = data.get('image')
        return char

#Events_________________________________________________________________________
@client.event
async def on_ready():
    print("I've awoken.")

@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            #Creates folder to store data in
            InitDirectory(guild)
            await channel.send('I have arrived!')
        break

#Functions______________________________________________________________________
def InitDirectory(guild):
    mode = 0o666
    folder = guild.name
    parent = 'Servers/'
    path = os.path.join(parent, folder)
    os.mkdir(path, mode)

    subFolder = 'Characters'
    parent = f'Servers/{guild.name}/'
    path = os.path.join(parent, subFolder)
    os.mkdir(path, mode)

def ConstructPath(guild):
    return f'Servers/{guild.name}/Characters/'

def ExportCharacter(char, guild):

    output = Path(f'{ConstructPath(guild)}{char.name}.txt')
    f = open(output, 'w')

    data = {
    "name": char.name,
    "xp": char.xp,
    "focuses": char.focuses,
    "image": char.image
    }

    f.writelines(json.dumps(data))
    f.close()

def FindCharacter(name, guild):
    file = Path(f'{ConstructPath(guild)}{name}.txt')

    if os.path.isfile(file):
        f = open(file, 'r')
        data = json.load(f)
        char = Character.Builder(data)
        return char
    else:
        return None

def CheckLevel(xp, focus=None):
    x = int(xp)
    if focus == None:
        return ((math.sqrt(x))/20) + 1
    else:
        if x < 10:
            return 0
        if x < 40 and x >= 10:
            return 1
        if x < 130 and x >= 40:
            return 2
        if x >= 130:
            return 3

async def VerifyCommand(ctx, name=None, xp=None, focus=None):

    if name == None:
        await ctx.send('Please specify a character')
        return False

    char = FindCharacter(name)
    if char == None:
        await ctx.send(f'There is no character by the name of {name}!')
        return False

    if xp == None:
        await ctx.send('Please specify amount of xp')
        return False
    else:
        try:
            f = int(xp)
        except:
            await ctx.send('xp must be a number!')
            return False

    if focus != None:
        try:
            f = int(focus)
            await ctx.send(f'The name of your focus cannot be a number! Try swapping the focus and the xp!')
            return False
        except:
            return True


    return True

def CreateImage(char=None, focus=None):
    backgound = Image.open('Images/card.png')

    #Checks if character include a portrait
    if char.image == None:
        icon = Image.open('Images/NoImage.png').convert("RGBA")
    else:
        f = requests.get(char.image, allow_redirects=True)
        open('tmp/image.png', 'wb').write(f.content)
        icon = Image.open('tmp/image.png').convert("RGBA")

    #Scales portrait to fit frame
    if icon.size[0] > icon.size[1]:
        size=(round(icon.size[0] * 160/icon.size[1]), 160)
    else:
        size=(160, round(icon.size[1] * 160/icon.size[0]))
    icon = icon.resize(size)


    #Checks for focus argument
    if focus == None:
        y = math.floor((CheckLevel(char.xp) + 1))
        needed = ((20*y) - 20)**2
        percent = (char.xp/needed) * 100
    else:
        y = CheckLevel(char.focuses[focus], focus) + 1
        if y == 1:
            needed = 10
        if y == 2:
            needed = 40
        if y >= 3:
            needed = 130
        percent = (int(char.focuses[focus])/needed) * 100

    #Sets length of progress bar
    rectangle = Image.open('Images/progress.png').resize(size)
    shadow = Image.open('Images/shadow.png').resize((size[0] + 15, size[1]))
    size = (round(rectangle.size[0] * percent / 100), rectangle.size[1])

    if size[0] == 0:
        size = (1, rectangle.size[1])


    #Pastes images togethor
    frame=Image.open('Images/frame.png')
    card2 = Image.open('Images/card2.png')
    backgound.paste(icon, (40,40), icon)
    backgound.paste(card2,(240,160),card2)
    backgound.paste(shadow, (240,160), shadow)
    backgound.paste(rectangle, (240,160), rectangle)
    backgound.paste(frame, (0,0), frame)

    #Time for some text!
    largeFont = ImageFont.truetype('Fonts/bahnschrift.tff', 40)
    smallFont = ImageFont.truetype('Fonts/bahnschrift.ttf', 20)

    nameplate = ImageDraw.Draw(backgound)
    xpneeded = ImageDraw.Draw(backgound)
    level = ImageDraw.Draw(backgound)

    if focus == None:
        text = f'{char.name}:'
        subtext = f'Character Level'

        xpneeded.text((920,135), f'{char.xp}/{needed} XP',
        font=smallFont, align='right', fill=(93,93,93), anchor="ra")

        level.text((960,16), f'Level: #{math.floor(CheckLevel(char.xp))}',
        font=largeFont, align='right', fill=(255,255,255), anchor="ra")

    else:
        text = f'{char.name}: {focus}'
        subtext = f'{focus}:'
        xpneeded.text((920,135), f'{char.focuses[focus]}/{needed} XP',
        font=smallFont, align='right', fill=(93,93,93), anchor="ra")

        level.text((960,16),
        f'Level: #{math.floor(CheckLevel(char.focuses[focus], focus))}',
        font=largeFont, align='right', fill=(255,255,255), anchor="ra")

    nameplate.text((240,90), text, font=largeFont, fill=(255,255,255))
    nameplate.text((240,135), subtext, font=smallFont, fill=(93,93,93))

    backgound.save('tmp/card.png')

#Commands_______________________________________________________________________
#Creates new character
@client.command(help=helpInfo[0], brief=helpInfo[1])
async def new(ctx, name):
    if name == None:
        await ctx.send('Please provide a name for your character!')
        return

    #Checks if character alrady exists
    if FindCharacter(name, ctx.guild) != None:
        await ctx.send('There is already a character with this name!')
        await ctx.send('Would you like to override it?\nY or N')

        msg = await client.wait_for('message', timeout=30)
        if msg.content == 'Y':
            await ctx.send('It has been done...')
        else:
            await ctx.send('Maybe next time.')
            return

    #Assigns values to new char instance.
    char = Character()
    char.name = name
    if len(ctx.message.attachments) > 0:
        if ctx.message.attachments[0].url.endswith('png') or ctx.message.attachments[0].url.endswith('jpg'):
            char.image = ctx.message.attachments[0].url

    ExportCharacter(char, ctx.guild)
    await ctx.send(f'Sucessfully created {name}!')

#Add xp to character
@client.command(help=helpInfo[2], brief=helpInfo[3])
async def add(ctx, name=None, xp=None, focus=None):

    if await VerifyCommand(ctx, name, xp, focus) == True:

        char = FindCharacter(name, ctx.guild)

        if focus == None:
            char.xp += int(xp)
            await ctx.send(f'Added {xp} xp to {char.name}.')
        else:
            if focus in char.focuses:
                i = int(char.focuses[focus])
                i += int(xp)
                char.focuses[focus] = i
            else:
                char.focuses.update({focus:xp})
            await ctx.send(f'Added {xp} xp to {focus} in {char.name}.')

        ExportCharacter(char)

 #Set xp to value
@client.command(help=helpInfo[4], brief=helpInfo[5])
async def set(ctx, name=None, xp=None, focus=None):
    if await VerifyCommand(ctx, name, xp, focus) == True:

        char = FindCharacter(name, ctx.guild)
        if focus == None:
            char.xp = int(xp)
            await ctx.send(f"Set {char.name}'s xp to {xp}.")
        else:
            if focus in char.focuses:
                char.focuses[focus] = xp
            else:
                char.focuses.update({focus:xp})

            await ctx.send(f"Set {char.name}'s xp for {focus} to {xp}.")

    ExportCharacter(char)

@client.command(help=helpInfo[6], brief=helpInfo[7])
async def level(ctx, name=None, focus=None):
    if name == None:
        await ctx.send('Please specify a character and/or focus')
        return

    char = FindCharacter(name, ctx.guild)
    if char == None:
        await ctx.send(f"No character by the name of {name} exists!")
        return

    if focus != None:
        if focus not in char.focuses:
            await ctx.send(f"No focus by the name of {focus} exists in {name}!")
            return

    CreateImage(char, focus)
    await ctx.send(file = discord.File('tmp/card.png'))

#Random Junk____________________________________________________________________
client.run('ODE4NTI1MjM4MTM5NTUxNzg0.YEZVCA._zla2E5ANn70JigmwbSCbzjbrqE')
