from discord import Permissions, Interaction
from discord.app_commands import MissingPermissions, check


def admin_or_common_server():
    perms = dict(administrator=True)
    invalid = perms.keys() - Permissions.VALID_FLAGS.keys()
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        if interaction.channel_id == 1072580369251041330:
            return True

        permissions = interaction.permissions

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return check(predicate)
