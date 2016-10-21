import discord
import twitter
import json
import database as db
import sys
import urllib.request

from time import gmtime, strftime
from yandex_translate import YandexTranslate

global client
global task

commands = ['ship', 'points', 'noeqa', 'debug']

with open('config.json') as data_file:
    config = json.load(data_file)

api = twitter.Api(consumer_key=config['twitter']['consumer_key'],
                  consumer_secret=config['twitter']['consumer_secret'],
                  access_token_key=config['twitter']['access_token_key'],
                  access_token_secret=config['twitter']['access_token_secret'])

translate = YandexTranslate(config['yandex']['token'])


async def call(func, msg):
    if func in commands:
        await globals()[func](msg)


# INTERN
def perm(author, perm_lvl):
    if author.top_role.name == "Admin":
        return True
    elif author.top_role.name == "Mod" and perm_lvl <= 2:
        return True
    elif perm_lvl == 1:
        return True
    else:
        return False

async def twitter():
    try:
        statuses = api.GetUserTimeline(screen_name='sega_pso2', count=1)
        if (statuses[0].id_str != db.d['last_tweet']):
            db.d['last_tweet'] = statuses[0].id_str
            trans = translate.translate(statuses[0].text, 'en')
            post = '*@sega_pso2 just tweeted:* \n\n'
            post += statuses[0].text + '\n'
            await send('twitter', post)
            post = '\n*translation:* \n\n'
            post += trans['text'][0] + '\n'
            await send('twitter', post)
    except:
        print(sys.exc_info()[0])


async def send(chname, msg, mention = None):
    await client.wait_until_ready()
    role_m = ''
    server = client.get_server(config['discord']['serverid'])
    channel = discord.utils.get(server.channels, name=chname)
    if (mention != None):
        roles = mention.strip().split(' ')
        for role in roles:
            if (role == 'default'):
                role_m += '@here '
            else:
                try:
                    role = discord.utils.get(server.roles, name=role)
                    role_m += role.mention + ' '
                except:
                    print(mention)
        await client.send_message(channel, role_m + msg)
    else:
        await client.send_message(channel, msg)

async def check_pso_playing():
    server = client.get_server(config['discord']['serverid'])
    for member in server.members:
        if (member.game is not None):
            if (member.game.name == 'Phantasy Star Online 2'
                    and str(member.status) == 'online'):
                    await give_points(member, 5)
        await check_lvlup(member)

async def check_lvlup(member):
    server = client.get_server(config['discord']['serverid'])
    newbie = discord.utils.get(server.roles, name='Newbie')
    rookie = discord.utils.get(server.roles, name='Rookie')
    member_r = discord.utils.get(server.roles, name='Member')
    veteran = discord.utils.get(server.roles, name='Veteran')
    master = discord.utils.get(server.roles, name='Master')

    if member.id + '_p' in db.d:
        if (db.d[member.id+'_p'] >= 1680 and member.top_role == newbie):
            await client.add_roles(member, rookie)
            await send('bot', member.mention +
                    ' Congratulation, you are no longer a Newbie :^)')
        if (db.d[member.id+'_p'] >= 6300 and member.top_role == rookie):
            await client.add_roles(member, member_r)
            await send('bot', member.mention +
                    ' You leveled up to Member!! ONE OF US ONE OF US')
        if (db.d[member.id+'_p'] >= 16800 and member.top_role == member_r):
            await client.add_roles(member, veteran)
            await send('bot', member.mention +
                    ' AYY Veteran already!! GRATZ :)')
        if (db.d[member.id+'_p'] >= 50400 and member.top_role == veteran):
            await client.add_roles(member, master)
            await send('bot', member.mention +
                    ' HOLY SHIT!! A NEW MASTER HAS RISEN! WOOP WOOP PARTY HARD')
    else:
        db.d[member.id + '_p'] = 0
        await sync_db()

async def checkeq():
    try:
        api_eq = urllib.request.urlopen("http://pso2emq.flyergo.eu/api/v2/")
        eq = json.loads(api_eq.read().decode('UTF-8'))
        eq = eq[0]
        eq_time = eq['jst']
        eq_text = eq['text'].splitlines()
        db.d['eqmention'] = ''
        if (eq_time != db.d['eq']):
            db.d['eq'] = eq_time
            count = 0
            count2 = 0
            await send('eqalert',
                       'In 1 hour the following EQs will start:')
            for line in eq_text:
                if line.startswith('[In Prep') or (count == 1 and count2 == 0):
                    if count == 0:
                        eq_name = line.split(' ', 3)[3].strip()
                        await send('eqalert', eq_name, 'default')
                        db.d['eqmention'] += 'default '
                    elif count == 1:
                        eq_name = line.strip()
                        await send('eqalert', eq_name, 'default')
                    count = 1
                elif (line[0:1].isdigit and line[2] == ':'):
                    if not (line[3] == '0' or line[3] == '3'):
                        eq_name = line.split(':')[1].strip()
                        if (eq_name != '-' and not eq_name.startswith('[Cooldown]') and not eq_name[0].isdigit()):
                            eq_mention_temp = 'ship' + line.split(':')[0].strip().lower()
                            db.d['eqmention'] += eq_mention_temp + ' '
                            await send('eqalert', ': ' +
                                       eq_name, eq_mention_temp)
                            count = 1
                            count2 = 1
            if (count == 0):
                await send('eqalert', 'None :(')
    except:
        print(sys.exc_info()[0])

async def sync_db():
    db.d.sync()

async def give_points(member, points):
    if member.id + '_p' in db.d:
        if points > 0:
            db.d[member.id + '_p'] += points
            await sync_db()
        elif points < 0:
            db.d[member.id + '_p'] = db.d[member.id + '_p'] + points
            await sync_db()
    else:
        db.d[member.id+'_p'] = points
        await sync_db()

async def log(msg):
    file_name = msg.author.name+'.txt'
    with open('log/'+file_name, 'a') as logfile:
        if msg.attachments != []:
            logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' '
                          + msg.channel.name+' '+msg.author.name + ': '
                          + msg.content+' '+msg.attachments[0]['url']+'\n')
        else:
            logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' '
                          + msg.channel.name+' '+msg.author.name + ': '
                          + msg.content+'\n')

    file_name = msg.channel.name + '.txt'
    with open('log/'+file_name, 'a') as logfile:
        if msg.attachments != []:
            logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' '
                          + msg.author.name + ': ' + msg.content+' '
                          + msg.attachments[0]['url']+'\n')
        else:
            logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' '
                          + msg.author.name + ': ' + msg.content+'\n')


# CHAT COMMANDS

async def ship(message):
    try:
        if (message.content.split(' ')[1].isdigit):
            server = client.get_server(config['discord']['serverid'])
            ship = discord.utils.get(server.roles, name='ship'
                                     + message.content.split(' ')[1])
            if (ship is not None):
                await client.add_roles(message.author, ship)
                await send('bot', message.author.mention
                           + ' you are now on '
                           + 'ship'+message.content.split(' ')[1] + '!')
    except:
        await client.send_message(message.channel,
                                  'ERROR: wrong command syntax')

async def points(message):
    try:
        if len(message.content.split(' ')) >= 2:
            if perm(message.author, 2):
                member = discord.utils.get(message.server.members,
                                           name=message.content.split(' ')[1])
                if len(message.content.split(' ')) == 2:
                    if member.id+'_p' in db.d:
                        await send('bot', member.name + ' has '
                                   + str(db.d[member.id + '_p']) + ' points!')
                    else:
                        db.d[member.id + '_p'] = 0
                        await sync_db()
                        await send('bot', member.name + ' has '
                                   + str(db.d[member.id + '_p']) + ' points!')
                elif len(message.content.split(' ')) == 3:
                    if member.id + '_p' in db.d:
                        n = int(message.content.split(' ')[2])
                        await give_points(member, n)
                        await send('bot', member.name + ' has '
                                   + str(db.d[member.id + '_p'])
                                   + ' points now!')
                    else:
                        db.d[member.id + '_p'] = 0
                        n = int(message.content.split(' ')[2])
                        await give_points(member, n)
                        await send('bot', member.name + ' has '
                                   + str(db.d[member.id + '_p'])
                                   + ' points now!')
            else:
                await client.send_message(message.channel,
                                          'ERROR: not enough permissions')
        else:
            await send('bot', message.author.mention +
                       ' You have ' + str(db.d[message.author.id + '_p'])
                       + ' points!')
    except:
        await client.send_message(message.channel,
                                  'ERROR: wrong command syntax')

async def noeqa(message):
    try:
        server = client.get_server(config['discord']['serverid'])
        newbie = discord.utils.get(server.roles, name='noeqa')
        await client.add_roles(message.author, newbie)
        await client.send_message(message.channel, message.author.mention
                                  + ' you will no longer get EQ Alerts.')
    except:
        await client.send_message(message.channel,
                                  'ERROR: wrong command syntax')

async def debug(message):
    if(perm(message.author, 2)):
        server = client.get_server(config['discord']['serverid'])
        for member in server.members:
            if (member.game is not None and str(member.status) == 'online'):
                if (member.game.name == 'Phantasy Star Online 2'):
                        await send('staff', member.name
                                   + ' is playing pso2 - okay')
                else:
                    await send('staff', member.name + ' is playing '
                               + member.game.name)
    else:
        await client.send_message(message.channel,
                                  'ERROR: not enough permissions')
