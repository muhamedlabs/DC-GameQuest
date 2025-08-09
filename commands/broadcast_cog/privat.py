import disnake
from disnake.ext import commands

class PrivateVoiceManager(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.special_channel_id = 1195867893938794651
        self.category_id = 1195867893938794649
        self.allowed_roles = [
            1195867892550479985, 1195867892550479984, 1195867892550479983,
            1195867892521123859, 1201172180558417931, 1196983887608426660,
            1195867892521123858, 1195867892521123857, 1195867892521123856
        ]
        self.bot_created_channels = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        guild = member.guild
        special_channel = guild.get_channel(self.special_channel_id)
        category = guild.get_channel(self.category_id)

        # Пользователь зашел в специальный канал
        if after.channel and after.channel.id == self.special_channel_id and category:
            overwrites = {
                guild.default_role: disnake.PermissionOverwrite(connect=False),
                member: disnake.PermissionOverwrite(
                    connect=True, manage_channels=True, move_members=True,
                    mute_members=True, deafen_members=True, create_instant_invite=True
                )
            }

            # Добавить владельца сервера
            server_owner = guild.get_member(guild.owner_id)
            if server_owner:
                overwrites[server_owner] = disnake.PermissionOverwrite(connect=True, manage_channels=True)

            # Добавить разрешенные роли
            for role_id in self.allowed_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = disnake.PermissionOverwrite(connect=True)

            # Создание нового голосового канала
            new_channel = await category.create_voice_channel(
                name=f"Лейтенант {member.name}",
                overwrites=overwrites
            )
            self.bot_created_channels[member.id] = new_channel
            await member.move_to(new_channel)

        # Проверка на удаление пустого канала
        if before.channel and before.channel.id != self.special_channel_id and len(before.channel.members) == 0:
            if before.channel.id in [ch.id for ch in self.bot_created_channels.values()]:
                await before.channel.delete()
                self.bot_created_channels = {
                    k: v for k, v in self.bot_created_channels.items() if v.id != before.channel.id
                }
