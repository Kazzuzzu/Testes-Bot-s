import discord
from discord.ext import commands
import requests
import random
from io import BytesIO
from PIL import Image

TOKEN = 'Token_Discord'

intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(command_prefix='!', intents=intents)


dominated_pokemon = {}
user_coins = {}

def get_random_pokemon_image():
    pokemon_id = random.randint(1, 898)
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        image_url = data['sprites']['front_default']
        return pokemon_id, image_url
    else:
        print(f"Erro ao obter dados do Pokémon: {response.status_code}")
        return None, None

def resize_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    
    new_width = img.width * 2
    new_height = img.height * 2
    img = img.resize((new_width, new_height), Image.LANCZOS)

    
    if img.mode != 'RGB':
        img = img.convert('RGB')

   
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command(name='pokemon')
async def pokemon(ctx):
    pokemon_id, image_url = get_random_pokemon_image()
    if pokemon_id and image_url:
        resized_image = resize_image(image_url)
        message = await ctx.send(file=discord.File(resized_image, 'pokemon.png'))

        
        reactions = ['✅', '❌', '☠️']
        for reaction in reactions:
            try:
                await message.add_reaction(reaction)
            except discord.errors.HTTPException:
                print(f"Erro ao adicionar a reação: {reaction}")

        
        dominated_pokemon[message.id] = {
            'pokemon_id': pokemon_id,
            'user_id': ctx.author.id,
            'confirmations': []
        }

    else:
        await ctx.send("Não foi possível obter a imagem do Pokémon. Tente novamente.")

@bot.command(name='meus')
async def meus(ctx):
    dominios = []
    if ctx.author.id in user_coins:
        dominios.append(f'Moedas: {user_coins[ctx.author.id]}')
    
    for message_id, data in dominated_pokemon.items():
        if data['user_id'] == ctx.author.id:
            pokemon_id = data['pokemon_id']
            url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                pokemon_name = data['name']
                dominios.append(f'Pokemon: {pokemon_name.capitalize()} (ID: {pokemon_id})')

    if dominios:
        dominios_str = '\n'.join(dominios)
        await ctx.send(f'Pokémons dominados por {ctx.author.name}:\n{dominios_str}')
    else:
        await ctx.send(f'Você não dominou nenhum Pokémon.')

@bot.event
async def on_raw_reaction_add(payload):
    
    if payload.message_id in dominated_pokemon:
        user_id = payload.user_id
        emoji = payload.emoji.name

        
        if emoji == '❌':
            
            if user_id == dominated_pokemon[payload.message_id]['user_id']:
                
                pokemon_id = dominated_pokemon[payload.message_id]['pokemon_id']
                sell_price = 200
                
                
                if user_id not in user_coins:
                    user_coins[user_id] = 0
                user_coins[user_id] += sell_price
                
                
                del dominated_pokemon[payload.message_id]

                
                await bot.get_channel(payload.channel_id).send(f'<@{user_id}> vendeu o pokemon por {sell_price} moedas.')

       
        elif emoji == '☠️':
            
            if user_id != dominated_pokemon[payload.message_id]['user_id']:
                
                if user_id not in dominated_pokemon[payload.message_id]['confirmations']:
                    dominated_pokemon[payload.message_id]['confirmations'].append(user_id)
                
               
                if len(dominated_pokemon[payload.message_id]['confirmations']) == 2:
                    
                    del dominated_pokemon[payload.message_id]
                    
                    
                    await bot.get_channel(payload.channel_id).send(f'O Pokémon foi excluído permanentemente.')

       
        elif emoji == '✅':
            if user_id == dominated_pokemon[payload.message_id]['user_id']:
                await bot.get_channel(payload.channel_id).send(f'<@{user_id}> capturou este Pokémon!')

            
            
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Comando não encontrado. Digite `!pokemon` para obter um novo Pokémon.')

bot.run(TOKEN)
