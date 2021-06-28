import os
import imghdr

import discord

import food

# from keep_alive import keep_alive

DISCUSSION_CHANNEL_ID = 715753002392223785  # general channel for people to post to
IMAGE_CHANNEL_ID = 722221344447791254  # bot managed channel

client = discord.Client()
error_messages = {}


@client.event
async def on_ready():
    print("I'm in")
    print(client.user)
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="porn")
    )


@client.event
async def on_message(og_msg: discord.Message):
    if og_msg.channel.id == DISCUSSION_CHANNEL_ID and len(og_msg.attachments) > 0:
        for item in og_msg.attachments:
            attachment_data = await item.read()
            if imghdr.what(None, h=attachment_data) in (
                "jpeg",
                "png",
                "gif",
                "bmp",
                "webp",
                "tiff",
            ):
                await og_msg.add_reaction(
                    "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}"
                )

                try:
                    is_food, labels = food.food(
                        data=(
                            # only use local data if less than 10 MB
                            attachment_data
                            if len(attachment_data) > 10000000
                            else None
                        ),
                        url=item.url,
                    )
                    labels = (
                        "{} ({:.1%})".format(label, score)
                        for label, score in labels.items()
                    )
                except food.FoodException as e:
                    print(e)
                    error_msg = await og_msg.channel.send(
                        "**An error occurred during food detection.**\nTo manually override the food check, react with \N{SLICE OF PIZZA}. To remove this message, react with \N{WASTEBASKET}."
                    )
                    error_messages[error_msg.id] = (og_msg, item, None)
                    await error_msg.add_reaction("\N{SLICE OF PIZZA}")
                    await error_msg.add_reaction("\N{WASTEBASKET}")
                    return

                if not is_food:
                    error_msg = await og_msg.channel.send(
                        "**Food was not detected!** (confidence > 70%)\nTo manually override the food check, react with \N{SLICE OF PIZZA}. To remove this message, react with \N{WASTEBASKET}.\nDetected Labels: `{}`".format(
                            "`, `".join(labels)
                        )
                    )
                    error_messages[error_msg.id] = (og_msg, item, labels)
                    await error_msg.add_reaction("\N{SLICE OF PIZZA}")
                    await error_msg.add_reaction("\N{WASTEBASKET}")
                    return

                # no errors, send image
                await post_image(og_msg, item, labels)


@client.event
async def on_reaction_add(reaction, user):
    msg = reaction.message
    if msg.id in error_messages.keys() and user == error_messages[msg.id][0].author:
        if reaction.emoji == "\N{WASTEBASKET}":
            og_msg = error_messages.pop(msg.id)[0]
            await og_msg.remove_reaction(
                "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}",
                client.user,
            )
            await msg.delete()
            return
        elif reaction.emoji == "\N{SLICE OF PIZZA}":
            og_msg, attachment, labels = error_messages.pop(msg.id)
            await msg.delete()
            await post_image(og_msg, attachment, labels)


async def post_image(og_msg, attachment, labels=None):
    await og_msg.remove_reaction(
        "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}", client.user
    )
    await og_msg.add_reaction("\N{THUMBS UP SIGN}")
    # or '\U0001f44d' or '👍'
    embed = discord.Embed(
        title="Sent by", description=og_msg.author.mention, color=0x00FF00
    )
    if labels:
        embed.add_field(
            name="Detected Tags", value=f"`{'`, `'.join(labels)}`", inline=False
        )
    channel = client.get_channel(IMAGE_CHANNEL_ID)
    fi = await attachment.to_file()
    await channel.send(file=fi)
    await channel.send(embed=embed)


# keep_alive()
token = os.environ.get("DISCORD_BOT_SECRET")
client.run(token)
