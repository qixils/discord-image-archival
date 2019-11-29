import discord
import datetime
import os
import re
import requests
import unicodedata

GUILD_ID = 316292239984951296 # server ID to archive
TOKENFILE = 'token.txt' # file containing your token (in the first line)
BOT_ACCOUNT = True # if you're running as a bot account or user account. use user accounts with caution (they violate TOS!)
EXTENSIONS = ['jpg', 'jpeg', 'gif', 'png', 'gifv', 'bmp', 'mp4'] # file extensions to download
TIMEOUT_TOLERANCE = 5 # seconds you want to wait before giving up on a download
DOWNLOAD_FOLDER = 'images' # where to download images

client = discord.Client()
reextenstions = '|'.join(EXTENSIONS)
research = r'(https?:(?:[/|.|\w|\s|-])*\.(?:'+reextenstions+r'))'
downloaded = {}

def slugify(value):
    """
    Function from https://github.com/django/django/blob/86a0231e0a087d4b909f76223cc55d5bbb673930/django/utils/text.py#L394
    Convert to ASCII. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

def get_nonexistant_path(fname_path):
    """
    Function from https://stackoverflow.com/a/43167607
    Get the path to a filename which does not exist by incrementing path.
    """
    if not os.path.exists(fname_path):
        return fname_path
    filename, file_extension = os.path.splitext(fname_path)
    i = 1
    new_fname = "{}-{}{}".format(filename, i, file_extension)
    while os.path.exists(new_fname):
        i += 1
        new_fname = "{}-{}{}".format(filename, i, file_extension)
    return new_fname

def makepath(path):
    """
    Creates the folders for a file.
    ie makes the folders 'images' & 'abc123' for input of 'images/abc123/file.png'.
    """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}#{client.user.discriminator}')
    for channel in client.get_guild(GUILD_ID).text_channels:
        try:
            async for message in channel.history(limit=None,after=datetime.datetime(2015,3,1)):

                # here is where you'd change how you want to store the files, ie by channel.id or message.author.name
                #key = message.channel.id # stores by channel id
                #key = message.author.id # stores by author id
                key = slugify(f"{message.author.name}#{message.author.discriminator} {message.author.id}")
                key2 = slugify(f"{channel.name} {channel.id}")
                pathbase = os.path.join(DOWNLOAD_FOLDER, key)

                if key not in downloaded:
                    downloaded[key] = {}
                if key2 not in downloaded[key]:
                    downloaded[key][key2] = []

                for attachment in message.attachments: # downloads all attachments to a message
                    url = attachment.url
                    if attachment.url.split('.')[::-1][0] in EXTENSIONS and url not in downloaded[key][key2]:
                        destpath = get_nonexistant_path(os.path.join(pathbase, attachment.filename))
                        downloaded[key][key2].append(url)
                        print(f'Archiving {url} to {destpath}')
                        makepath(destpath)
                        await attachment.save(destpath)

                imglinks = re.findall(research, message.content)
                for img in imglinks: # downloads all images linked in a message
                    if img not in downloaded[key][key2]:
                        downloaded[key][key2].append(img)
                        # omg i'm reusing code i'm sinning
                        destpath = get_nonexistant_path(os.path.join(pathbase, img.split('/')[::-1][0]))
                        print(f'Archiving {img} to {destpath}')
                        makepath(destpath)
                        try:
                            r = requests.get(img, timeout=TIMEOUT_TOLERANCE)
                            with open(destpath, 'wb') as f:
                                f.write(r.content)
                        except: #too many exceptions to catch individually, sue me
                            print("Link errored, skipping.")
        except discord.errors.Forbidden:
            print('Skipping channel, lacking read message permissions')
    print('Completed!')
    await client.logout()

client.run(open(TOKENFILE,'r').read().split('\n')[0], bot=BOT_ACCOUNT)
