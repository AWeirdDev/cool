import discord
import discord.ui as ui


class PlayerView(ui.View):
    def __init__(self, *, paused: bool = False, skip_playlist: bool = False):
        super().__init__(
            ui.Button(
                style=(
                    discord.ButtonStyle.gray if not paused else discord.ButtonStyle.red
                ),
                label="  " if not paused else "Paused",
                custom_id=("pause" if not paused else "resume"),
                emoji=(
                    "<:pause:1265996604587118673>"
                    if not paused
                    else "<:play:1266005504619184229>"
                ),
            ),
            ui.Button(
                style=discord.ButtonStyle.gray,
                label="  ",
                custom_id="stop",
                emoji="<:octagon:1266010248804827176>",
            ),
            ui.Button(
                style=discord.ButtonStyle.gray,
                label="  ",
                custom_id="skip",
                emoji="<:skip:1266005302713651291>",
            ),
            ui.Button(
                style=discord.ButtonStyle.gray,
                label="  ",
                custom_id="skip-playlist",
                emoji="<:listend:1266336775232553071>",
                disabled=True,
            ),
        )
