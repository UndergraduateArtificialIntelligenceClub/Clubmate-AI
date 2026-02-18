"""
Role-based permission checks for Clubmate AI.
Exec role name is configured in settings and set via the dashboard.
"""

import discord
from discord import app_commands
from config import settings


def is_exec(interaction: discord.Interaction) -> bool:
    """Return True if the interaction user has the configured exec role."""
    if not isinstance(interaction.user, discord.Member):
        return False
    exec_role = settings.exec_role_name.lower()
    return any(r.name.lower() == exec_role for r in interaction.user.roles)


def exec_only():
    """
    App command check decorator — restricts a slash command to exec role members.
    Usage:
        @app_commands.check(exec_only())
        async def my_command(interaction): ...
    """
    def predicate(interaction: discord.Interaction) -> bool:
        if not is_exec(interaction):
            raise app_commands.CheckFailure(
                f"This command requires the **{settings.exec_role_name}** role."
            )
        return True
    return app_commands.check(predicate)
