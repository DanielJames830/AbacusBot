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

#Classes________________________________________________________________________
class Character:
    name = "John"
    xp = 0
    focuses = {
        'Name': 0
    }
    image = None

    def Builder(data):
        char = Character()
        char.name = data.get('name')
        char.xp = data.get('xp')
        char.focuses = data.get('focuses')
        char.image = data.get('image')
        return char

class Formula:
    def __init__(self):
        self._formula = open('Formulas/formula.txt', 'r').read()
        self._focusformula = open('Formulas/focusformula.txt', 'r').read()

    def get_formula(self):
        return self._formula

    def set_formula(self, a):
         self._formula = a

    def del_formula(self):
         del self._formula

    formula = property(get_formula, set_formula, del_formula)

    def get_focusformula(self):
        return self._focusformula

    def set_focusformula(self, a):
         self._focusformula = a

    def del_focusformula(self):
         del self._focusformula

    focusformula = property(get_focusformula, set_focusformula, del_focusformula)

#Events_________________________________________________________________________
@client.event
async def on_ready():
    print("I've awoken.")

#Functions______________________________________________________________________
def ExportCharacter(char):
    print(f'Exporting {char.name}.')
    file = Path(f'Characters/{char.name}.txt')
    f = open(file, 'w')

    data = {
    "name": char.name,
    "xp": char.xp,
    "focuses": char.focuses,
    "image": char.image
    }

    f.writelines(json.dumps(data))
    f.close()
    print(f'Exporting succeeded.')

def FindCharacter(name):
    print(f'Searching for {name}.')
    file = Path(f'Characters/{name}.txt')

    if os.path.isfile(file):
        f = open(file, 'r')
        data = json.load(f)
        char = Character.Builder(data)
        print(f'Found {name}.')
        return char
    else:
        print(f'Could not find {name}.')
        return None

def CheckLevel(xp, focus=None):
    print(f"Calculating level.....")
    x = int(xp)
    if focus == None:
        f = Formula()
        code = parser.expr(f.formula).compile()
        x = xp
        return eval(code)
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
    print(f"Generating {char.name}'s card.")
    backgound = Image.open('Images/card.png')

    print(f"Checking for image.")
    if char.image == None:
        print(f"No image found.")
        icon = Image.open('Images/NoImage.png').convert("RGBA")
    else:
        print(f"Image found!")
        f = requests.get(char.image, allow_redirects=True)
        open('tmp/image.png', 'wb').write(f.content)
        icon = Image.open('tmp/image.png').convert("RGBA")

    print(f"Scaling image.")
    if icon.size[0] > icon.size[1]:
        size=(round(icon.size[0] * 160/icon.size[1]), 160)

    else:
        size=(160, round(icon.size[1] * 160/icon.size[0]))
    icon = icon.resize(size)

    rectangle = Image.open('Images/progress.png')
    shadow = Image.open('Images/Shadow.png')

    print(f"Checking level progress.")
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


    size = (round(rectangle.size[0] * percent / 100), rectangle.size[1])

    if size[0] == 0:
        size = (1, rectangle.size[1])

    rectangle = rectangle.resize(size)
    shadow = shadow.resize((size[0] + 15, size[1]))

    print(f"Formatting text.")
    frame=Image.open('Images/frame.png')
    card2 = Image.open('Images/card2.png')
    backgound.paste(icon, (40,40), icon)
    backgound.paste(card2,(240,160),card2)
    backgound.paste(shadow, (240,160), shadow)
    backgound.paste(rectangle, (240,160), rectangle)
    backgound.paste(frame, (0,0), frame)

    largeFont = ImageFont.truetype('C:/Windows/Fonts/Bahnschrift.ttf', 40)
    smallFont = ImageFont.truetype('C:/Windows/Fonts/Bahnschrift.ttf', 20)

    nameplate = ImageDraw.Draw(backgound)
    xpneeded = ImageDraw.Draw(backgound)
    level = ImageDraw.Draw(backgound)

    if focus == None:
        text = f'{char.name}:'
        subtext = f'Character Level'
        xpneeded.text((920,135), f'{char.xp}/{needed} XP', font=smallFont, align='right', fill=(93,93,93), anchor="ra")
        level.text((960,16), f'Level: #{math.floor(CheckLevel(char.xp))}', font=largeFont, align='right', fill=(255,255,255), anchor="ra")
    else:
        text = f'{char.name}: {focus}'
        subtext = f'{focus}:'
        xpneeded.text((920,135), f'{char.focuses[focus]}/{needed} XP', font=smallFont, align='right', fill=(93,93,93), anchor="ra")
        level.text((960,16), f'Level: #{math.floor(CheckLevel(char.focuses[focus], focus))}', font=largeFont, align='right', fill=(255,255,255), anchor="ra")

    nameplate.text((240,90), text, font=largeFont, fill=(255,255,255))
    nameplate.text((240,135), subtext, font=smallFont, fill=(93,93,93))




    backgound.save('tmp/card.png')
    print(f"Image generation succeeded!")

#Commands_______________________________________________________________________
@client.command                                                                 (help="Creates a new file for the character specified. Send an image as an attachment for a profile picture. (Image must be an attachment, not a link.)", brief="Creates new character.")
async def new(ctx, name=None): #Create new character

    print(f'\nNew character request by {ctx.author}.')
    if name == None:
        await ctx.send('Please provide a name for your character!')
        print(f'Aborted character creation.')
        return

    char = Character()
    char.name = name

    if FindCharacter(char.name) != None:
        await ctx.send('This character already exists! Would you like to override it?\nY or N')
        msg = await client.wait_for('message', timeout=30)
        if msg.content == 'Y':
            await ctx.send('It has been done...')
        else:
            print(f'Aborted character creation.')
            return
    if len(ctx.message.attachments) > 0:
        if ctx.message.attachments[0].url.endswith('png') or ctx.message.attachments[0].url.endswith('jpg'):
            char.image = ctx.message.attachments[0].url

    ExportCharacter(char)
    print(f'Sucessfully created character!')
    await ctx.send(f'Sucessfully created {name}!')

@client.command                                                                 (help="Adds xp to a character or a focus. Leave the focus field blank to add to the overall level.", brief="Adds xp to the character.")
async def add(ctx, name=None, xp=None, focus=None): #Add xp to character
    print(f'\nAttempting to add xp to {name}.')
    if await VerifyCommand(ctx, name, xp, focus) == True:

        char = FindCharacter(name)

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

@client.command                                                                 (help="Sets the xp of a character or focus to amount specified. Leave the focus field blank to add to the overall level.", brief="Sets amount of xp.")
async def set(ctx, name=None, xp=None, focus=None): #Set xp to value
    print(f'\nAttempting to set xp of {name} to {xp}.')
    if await VerifyCommand(ctx, name, xp, focus) == True:
        char = FindCharacter(name)
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

@client.command                                                                 (help="Prints the current level of the character or focus specified. Leave the focus field blank to print the overall level.", brief="Displays character levels.")
async def level(ctx, name=None, focus=None):
    print(f'\nAttempting to generate image.')
    if name == None:
        await ctx.send('Please specify a character and/or focus')
        return
    if FindCharacter(name) == None:
        await ctx.send(f"No character by the name of {name} exists!")
        return

    char = FindCharacter(name)

    if focus != None:
        if focus in char.focuses:
            print('Found')
        else:
            await ctx.send(f"No focus by the name of {focus} exists in {name}!")
            return

    CreateImage(char, focus)
    await ctx.send(file = discord.File('tmp/card.png'))

#Random Junk____________________________________________________________________
client.run('ODE4NTI1MjM4MTM5NTUxNzg0.YEZVCA._zla2E5ANn70JigmwbSCbzjbrqE')
