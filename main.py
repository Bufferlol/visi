import discord
import json
import asyncio
#import function as f
import _mysql

client = discord.Client()
#f.client = client

with open('config.json') as data_file:
    config = json.load(data_file)

db=_mysql.connect('localhost', config['db']['user'],config['db']['pw'], config['db']['db'])

db.query("""SELECT server_id, discord_token, yandex_token, twitter_ck, twitter_cs, twitter_tk, twitter_ts FROM config LIMIT 1""")

r=db.store_result().fetchonce()

async def main():
    await client.wait_until_ready()
    while 1:
        await f.checkeq()
        await f.twitter()
        await asyncio.sleep(60)

async def points():
    await client.wait_until_ready()
    while 1:
        await f.check_pso_playing()
        await f.sync_db()
        await asyncio.sleep(300)


@client.async_event
async def on_message(message):
    await f.log(message)
    await f.give_points(message.author, 2)
    if message.content != '':
        if message.content[0] == '!':
            await f.call(message.content.split(' ')[0][1:], message)


@client.async_event
async def on_member_join(member):
    server = client.get_server(r['server_id'])
    newbie = discord.utils.get(server.roles, name='Newbie')
    await client.add_roles(member, newbie)
    await f.send('general', member.mention+' Welcome! :)')


@client.async_event
async def on_channel_update(a, b):
    await f.send('staff', 'CH: '+a.name+' Pos: '+str(a.position)+' -> CH: '
                 + b.name+' Pos: '+str(b.position))


@client.async_event
async def on_channel_create(a):
    await f.send('staff', 'CH: '+a.name+' Pos: '+str(a.position) +
                 ' created.')

@client.async_event
async def on_channel_delete(a):
    await f.send('staff', 'CH: '+a.name+' Pos: '+str(a.position)
                 + ' deleted.')


@client.async_event
async def on_member_remove(a):
    await f.send('staff', a.name+' left the server.')


@client.async_event
async def on_member_update(a, b):
    if a.nick is None:
        a.nick = a.name
    if b.nick is None:
        b.nick = b.name
    if a.nick != b.nick:
        await f.send('staff', a.nick+' -> '+b.nick)


@client.async_event
async def on_member_ban(a):
    await f.send('staff', a.name+' got banned.')

client.loop.create_task(main())
client.loop.create_task(points())
client.run(r['discord_token'])
