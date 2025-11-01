import sys
from mcp.server.fastmcp import FastMCP
from types import FibInput, TextInput


mcp = FastMCP("Demo")


@mcp.tool()
def print_ascii_minion() -> str:
    return '''
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
⠀⠀⠀⠀⠀⠀⠀⠛⠛⠁⠈⠛⠛⠀⠀⠀⠀⠀⠀⠀'''


# referencing this for making events on google calendar
# https://github.com/googleworkspace/python-samples/blob/main/calendar/quickstart/quickstart.py

# @mcp.resource("calendar://{today}")
# def DumpGcalEvents(today: str) -> str:
#     return ""
# nahhhh this is for later. i wanna build something dumb :)



@mcp.tool()
def call_fib(n: FibInput):
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

    return nth_fibonnaci(n, cache)


@mcp.prompt()
def rot13er(text: TextInput):

    if not text.isprintable():
        return "provided `text` contains non-printable characters."

    cipher = "".join(c+13 for c in text)

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
    return f"\"{substring}\" {text}"


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
    mcp.run(transport="streamable-http", mount_path="/mcp") # needs to be streamable-http so it can be hit by the gemini client via the url
