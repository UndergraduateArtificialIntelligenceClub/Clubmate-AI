import sys
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from customtypes import ROLES, FibInput, TextInput
from db import (
    Meeting,
    User,
    add_meeting_to_db,
    add_user_to_db,
    get_user_from_db,
    list_users_from_db,
)

mcp = FastMCP("Demo")


@mcp.tool()
def print_ascii_minion() -> str:
    return """
⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣴⠾⠛⠉⠉⠉⠉⠛⠿⣦⡀⠀⠀⠀⠀
⠀⠀⠀⢠⡿⠁⠀⢀⣠⣤⣤⣄⡀⠀⠈⢿⡆⠀⠀⠀
⠀⠀⢀⣿⣁⣀⣠⡿⠋⠀⠀⠙⢿⣄⣀⣈⣿⡀⠀⠀
⠀⠀⢸⣿⠛⠛⢻⣧⠀⠿⠇⠀⣼⡟⠛⠛⣿⡇⠀⠀
⠀⠀⢸⣿⠀⠀⠀⠙⢷⣦⣴⡾⠋⠀⠀⠀⣿⡇⠀⠀
⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠀⠀⣸⣿⠀⠀⠀⠛⠷⠶⠶⠾⠛⠀⠀⠀⣿⣇⠀⠀
⠀⣸⣿⣿⢷⣦⣀⣀⣀⣀⣀⣀⣀⣀⣴⡾⣿⣿⣇⠀
⢠⣿⢸⣿⠀⣿⡏⠉⠉⠉⠉⠉⠉⢹⣿⠀⣿⡇⣿⡄
⢸⡏⢸⣿⣀⣿⡇⠀⠀⠀⠀⠀⠀⢸⣿⣀⣿⡇⢹⡇
⢸⡇⠀⢿⣏⠉⠁⠀⠀⠀⠀⠀⠀⠈⠉⣹⡿⠀⢸⡇
⢸⣿⣤⣌⠛⠷⣶⣶⣶⣶⣶⣶⣶⣶⠾⠛⣡⣤⣿⡇
⠘⠿⠿⠇⠀⠀⠀⢿⡾⠇⠸⢷⡿⠀⠀⠀⠸⠿⠿⠃
⠀⠀⠀⠀⠀⠀⠀⠛⠛⠁⠈⠛⠛⠀⠀⠀⠀⠀⠀⠀"""


# referencing this for making events on google calendar
# https://github.com/googleworkspace/python-samples/blob/main/calendar/quickstart/quickstart.py

# @mcp.resource("calendar://{today}")
# def DumpGcalEvents(today: str) -> str:
#     return ""
# nahhhh this is for later. i wanna build something dumb :)


@mcp.tool()
async def dump_users() -> Optional[set[str]]:
    try:
        return await list_users_from_db()
    except Exception as e:
        print(f"Exception occurred trying to list all users: {e}")


# test gemini input: hi i want to add a user with requestee id of 2093480293, my requester id is 123456789012345678. the name of this user is carl, their email is dookie@ualberta.ca, their role is 1, and their username is weewoo
@mcp.tool()
async def add_user(
    requester_discord_id: str,
    requestee_discord_id: str,
    username: str,
    role: int,
    email: str,
    name: str,
):  # use discord_id retrieved via discord bot to lookup in database the role of user wanting to add a role
    # note here, requester_discord_id is the user wanting to add another user
    # requestee_discord_id is the user to be added
    try:
        requester = await get_user_from_db(requester_discord_id)
        if requester.role == ROLES.admin:
            user = User(
                username=username,
                role=role,
                discord_id=requestee_discord_id,
                email=email,
                name=name,
            )
            await add_user_to_db(user)
        else:
            return "Unauthorized... what are you doing you sussybaka"

    except Exception as e:
        return (
            f"Unable to add user with discord_id: {requestee_discord_id} due to => {e}"
        )


@mcp.tool()
def call_fib(input: FibInput):
    cache = {}
    sys.setrecursionlimit(8000)

    def nth_fibonnaci(n: int, cache: dict) -> int:
        print(n)
        if n <= 0:
            return 0
        if n == 1:
            return 1
        if n in cache:
            return cache[n]

        cache[n] = nth_fibonnaci(n - 1, cache) + nth_fibonnaci(n - 2, cache)
        return cache[n]

    return nth_fibonnaci(input.n, cache)


@mcp.prompt()
def rot13er(text: TextInput):

    if not text.t.isprintable():
        return "provided `text` contains non-printable characters."

    cipher = "".join(str(ord(c) + 13) for c in text.t)  # Bruh what did I write before

    # Return a prompt or boolean
    return f"{cipher}"


@mcp.prompt()
def check_occurrence(text: str, substring: str):
    """
    Checks if `substring` occurs in `text`,
    and ensures both contain only visible/printable characters.
    """

    # Validate printable characters
    if not text.isprintable():
        return "provided `text` contains non-printable characters."
    if not substring.isprintable():
        return "provided `substring` contains non-printable characters."

    # Return a prompt or boolean
    return f'"{substring}" {text}'


@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", mount_path="/mcp"
    )  # needs to be streamable-http so it can be hit by the gemini client via the url
