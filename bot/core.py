import asyncio
import os
from typing import Annotated, Optional

import discord
from discord import Bot

from .states.clients import Client, Clients
from .states.queue import Queue, Canditate

from .music import acreate_source, asearch
from .spotify import Spotify
from .views import PlayerView

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(intents=intents)
clients = Clients()
spotify = Spotify(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.slash_command(name="play", description="Play music.")
async def play(
    ctx: discord.ApplicationContext,
    query: Annotated[str, discord.Option(description="The query.")],
):
    assert ctx.guild

    if not ctx.author.voice:  # type: ignore
        return await ctx.respond("You are not in a voice channel.", ephemeral=True)

    if not ctx.guild.me.voice:  # type: ignore
        vc = await ctx.author.voice.channel.connect()  # type: ignore
    else:
        client = clients.get(ctx.guild.id)

        if not client:
            try:
                vc = await ctx.guild.me.voice.channel.connect()  # type: ignore
            except discord.errors.ClientException as e:
                print(e)
                return await ctx.respond(
                    "Hmm, I've connected to a voice channel?", ephemeral=True
                )

        else:
            vc = client.vc

    await ctx.interaction.response.defer(invisible=False)
    text = await create_player(ctx, vc, query)

    if text:
        await ctx.interaction.followup.send(text)
    elif text != "ok":
        try:
            print("removing clients from L69")
            clients.remove(ctx.guild.id)
        except KeyError:
            pass


async def create_player(
    ctx: discord.ApplicationContext,
    vc: discord.VoiceClient,
    query: str,
    *,
    playlist_id: Optional[str] = None,
):
    assert ctx.guild

    if query.startswith("https://open.spotify.com/playlist/"):
        d = await spotify.get_playlist(query)
        await ctx.interaction.followup.send(
            f"<a:loading:1266328605978525789>  Adding songs from **{d['name']}** to queue in background...\n\n"
            "-# Don't worry, songs are loaded on-demand."
        )

        i = 0
        print(d["id"])
        for song in d["tracks"]["items"]:
            result = song["track"]
            if "show" in result:
                continue

            await create_player(
                ctx,
                vc,
                query=(
                    ", ".join([a["name"] for a in result["artists"]])
                    + " - "
                    + result["name"]
                ),
                playlist_id=d["id"],
            )

            i += 1

        await ctx.channel.send(  # type: ignore
            f":white_check_mark: Added **{i}** songs from **{d['name']}** to queue!"
        )

        return "ok"

    elif query.startswith("https://open.spotify.com/track/"):
        return "no"

    try:
        result = await asearch(query)
        source = await acreate_source(result["link"])
    except Exception:
        if not clients.get(ctx.guild.id):
            clients.add(ctx.guild.id, Client(vc=vc, queue=Queue()))

        return f"Could not find **{query}** (or age restrictive content)"

    player = discord.FFmpegPCMAudio(
        source,
        **FFMPEG_OPTIONS,  # type: ignore
    )
    client = clients.get(ctx.guild.id)

    if not client:
        clients.add(ctx.guild.id, Client(vc=vc, queue=Queue()))
        client = clients.clients[ctx.guild.id]

    queue = client.queue
    queue.append(
        Canditate(
            source=player,
            title=result["title"],
            thumbnail=result["thumbnails"][0]["url"],
            query=query,
            duration=result["duration"],
            linked_playlist=playlist_id,
        )
    )

    if queue.len() == 1:
        await go(ctx, vc)  # type: ignore

    return f"Added **{result['title']}** to queue"


@bot.slash_command(name="pause", description="Pause music.")
async def pause(ctx: discord.ApplicationContext):
    await ctx.interaction.response.defer(invisible=True)
    assert ctx.guild_id
    client = clients.get(ctx.guild_id)

    if client and client.vc:
        client.vc.pause()
        client.lyrics_flags = asyncio.Event()

        if client.player_message:
            await client.player_message.edit(view=None)

        await ctx.interaction.followup.send("<:pause:1265996604587118673> Paused!")
    else:
        await ctx.interaction.followup.send("Hmm...?", ephemeral=True)


@bot.slash_command(name="resume", description="Resume music.")
async def resume(ctx: discord.ApplicationContext):
    await ctx.interaction.response.defer(invisible=True)
    assert ctx.guild_id
    client = clients.get(ctx.guild_id)

    if client and client.vc:
        client.vc.resume()
        if client.lyrics_flags:
            client.lyrics_flags.set()

        if client.player_message:
            await client.player_message.edit(view=None)

        await ctx.interaction.followup.send("<:play:1266005504619184229> Resumed!")
    else:
        await ctx.interaction.followup.send("Hmm...?", ephemeral=True)


@bot.slash_command(name="nowplaying", description="Show the music player.")
async def nowplaying(ctx: discord.ApplicationContext):
    await ctx.interaction.response.defer(invisible=True)
    assert ctx.guild_id
    client = clients.get(ctx.guild_id)

    if client and client.vc:
        if client.player_message:
            await client.player_message.edit(view=None)

        await ctx.interaction.followup.send(
            embed=client.player_message.embeds[0],  # type: ignore
            view=PlayerView(paused=client.vc.is_paused()),
        )
    else:
        await ctx.interaction.followup.send("Hmm...?", ephemeral=True)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data and interaction.data.get("custom_id"):
        custom_id = interaction.data["custom_id"]  # type: ignore

        if custom_id in {"pause", "resume"}:
            assert interaction.guild_id
            client = clients.get(interaction.guild_id)

            if client and client.vc:
                if (
                    client.player_message
                    and interaction.message
                    and client.player_message.id != interaction.message.id
                ):
                    return await interaction.response.defer(invisible=True)

                if custom_id == "pause":
                    client.vc.pause()
                    client.lyrics_flags = asyncio.Event()

                else:
                    client.vc.resume()
                    if client.lyrics_flags:
                        client.lyrics_flags.set()
                    else:
                        client.lyrics_flags = None

                await interaction.response.edit_message(
                    view=PlayerView(paused=custom_id == "pause")
                )

        elif custom_id == "skip":
            assert interaction.guild_id
            client = clients.get(interaction.guild_id)

            if client and client.vc:
                if (
                    client.player_message
                    and interaction.message
                    and client.player_message.id != interaction.message.id
                ):
                    return await interaction.response.defer(invisible=True)

                await interaction.response.edit_message(view=None)
                client.vc.stop()
                print("removing clients from custom_id == skip")

        elif custom_id == "stop":
            assert interaction.guild_id
            client = clients.get(interaction.guild_id)

            if client and client.vc:
                if (
                    client.player_message
                    and interaction.message
                    and client.player_message.id != interaction.message.id
                ):
                    return await interaction.response.defer(invisible=True)

                await interaction.response.edit_message(view=None)
                await client.vc.disconnect()
                print("removing clients from custom_id == stop")
                clients.remove(interaction.guild_id)

        elif custom_id == "skip-playlist":
            assert interaction.guild_id
            client = clients.get(interaction.guild_id)

            if client and client.vc:
                if (
                    client.player_message
                    and interaction.message
                    and client.player_message.id != interaction.message.id
                ):
                    return await interaction.response.defer(invisible=True)

                await interaction.response.defer(invisible=True)
                current = client.queue.next()
                assert current

                linked_playlist = current.linked_playlist

                for item in client.queue.items.copy():
                    print(item.linked_playlist, linked_playlist)
                    if linked_playlist == item.linked_playlist:
                        client.queue.pop()

                    print(client.queue.items)

                client.vc.stop()

    await bot.process_application_commands(interaction)


def after_leave(e, ctx: discord.ApplicationContext, vc: discord.VoiceClient):
    print("errors:", e)

    assert ctx.guild

    client = clients.get(ctx.guild.id)
    if client and client.lyrics_task:
        client.lyrics_task.cancel()
        client.lyrics_task = None

    if client and client.player_progress_task:
        client.player_progress_task.cancel()
        client.player_progress_task = None

    if client and client.player_message:
        bot.loop.create_task(client.player_message.edit(view=None))

    if client and client.queue.blank:
        print("queue is blank, removing client from after_leave")
        clients.remove(ctx.guild.id)
        return bot.loop.create_task(vc.disconnect())

    if vc.is_connected():
        bot.loop.create_task(go(ctx, vc, pop=True))


async def go(
    ctx: discord.ApplicationContext, vc: discord.VoiceClient, *, pop: bool = False
):
    assert ctx.guild

    c = clients.get(ctx.guild.id)

    if not c:
        print("removing client from L341")
        clients.remove(ctx.guild.id)
        return await vc.disconnect()

    queue = c.queue

    if pop:
        queue.pop()

    canditate = queue.next()

    if not canditate:
        return await vc.disconnect()

    player = canditate.source
    title = canditate.title
    thumbnail = canditate.thumbnail

    message = await ctx.channel.send(  # type: ignore
        embed=(
            discord.Embed(
                title=title,
                color=0x0995EC,
                thumbnail=thumbnail,
            ).add_field(name="Duration", value=canditate.duration)
        ),
        view=PlayerView(skip_playlist=bool(canditate.linked_playlist)),
    )

    def play():
        vc.play(
            player,
            after=lambda e: after_leave(e, ctx, vc),
        )

    play()
    client = Client(vc, queue=queue, player_message=message)
    clients.add(ctx.guild.id, client)
    queue.items[0].client = client
