"""
Test script demonstrating Gemini MCP Client usage
Shows various features and capabilities
"""

import asyncio
import os
from dotenv import load_dotenv
from gemini_mcp_client import GeminiMCPClient

load_dotenv()


async def test_basic_chat():
    """Test basic chat functionality"""
    print("=" * 50)
    print("TEST 1: Basic Chat")
    print("=" * 50)

    client = GeminiMCPClient()

    try:
        # Add example server
        client.add_server(
            "example",
            "./example_server.py",
            language="python",
            description="Example MCP server with utilities",
        )

        # Connect
        await client.connect("example")
        print("✓ Connected to example server")

        # Get tools
        tools = await client.get_tools()
        print(f"✓ Found {len(tools)} tools: {', '.join(tools.keys())}")

        # Chat
        response = await client.chat("What tools are available on this server?")
        print(f"\nGemini: {response[:200]}...")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_conversation_history():
    """Test conversation history"""
    print("\n" + "=" * 50)
    print("TEST 2: Conversation History")
    print("=" * 50)

    client = GeminiMCPClient()

    try:
        client.add_server("example", "./example_server.py")
        await client.connect("example")

        # Multi-turn conversation
        prompts = ["What is 10 + 5?", "Double that number", "Now subtract 3"]

        for prompt in prompts:
            response = await client.chat(prompt)
            print(f"You: {prompt}")
            print(f"Gemini: {response[:100]}...\n")

        # Show history
        history = client.get_conversation_history()
        print(f"✓ Conversation history ({len(history)} messages):")
        for i, msg in enumerate(history, 1):
            preview = (
                msg["content"][:50] + "..."
                if len(msg["content"]) > 50
                else msg["content"]
            )
            print(f"  {i}. [{msg['role'].upper()}] {preview}")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_server_management():
    """Test server configuration management"""
    print("\n" + "=" * 50)
    print("TEST 3: Server Management")
    print("=" * 50)

    client = GeminiMCPClient()

    try:
        # Add multiple servers
        client.add_server("server1", "./example_server.py", description="First server")
        client.add_server("server2", "./example_server.py", description="Second server")

        # List servers
        servers = client.list_servers()
        print(f"✓ Registered servers: {servers}")

        # Get server info
        for server_name in servers:
            config = client.servers[server_name]
            print(f"\n  {server_name}:")
            print(f"    Path: {config.script_path}")
            print(f"    Language: {config.language}")
            print(f"    Description: {config.description}")

        # Remove a server
        client.remove_server("server2")
        print(f"\n✓ Removed server2")
        print(f"✓ Remaining servers: {client.list_servers()}")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_tool_discovery():
    """Test tool discovery and listing"""
    print("\n" + "=" * 50)
    print("TEST 4: Tool Discovery")
    print("=" * 50)

    client = GeminiMCPClient()

    try:
        client.add_server("example", "./example_server.py")
        await client.connect("example")

        # Get tools
        tools = await client.get_tools()

        print(f"✓ Discovered {len(tools)} tools:")
        for tool_name, tool_obj in tools.items():
            print(f"\n  • {tool_name}")
            if hasattr(tool_obj, "description"):
                print(f"    Description: {tool_obj.description}")
            if hasattr(tool_obj, "inputSchema"):
                schema = tool_obj.inputSchema
                if hasattr(schema, "properties"):
                    props = schema.properties
                    print(
                        f"    Parameters: {', '.join(props.keys()) if props else 'None'}"
                    )

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 50)
    print("TEST 5: Error Handling")
    print("=" * 50)

    client = GeminiMCPClient()

    # Test 1: Invalid server
    try:
        print("Testing invalid server path...")
        client.add_server("invalid", "/nonexistent/path.py")
        print("✗ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✓ Correctly raised FileNotFoundError for invalid path")

    # Test 2: Invalid language
    try:
        print("Testing invalid language...")
        client.add_server("invalid", "./example_server.py", language="rust")
        print("✗ Should have raised ValueError")
    except ValueError:
        print("✓ Correctly raised ValueError for invalid language")

    # Test 3: Not connected
    try:
        print("Testing operations without connection...")
        await client.get_tools()
        print("✗ Should have raised ValueError")
    except ValueError:
        print("✓ Correctly raised ValueError when not connected")

    await client.close()


async def test_configuration_persistence():
    """Test configuration file persistence"""
    print("\n" + "=" * 50)
    print("TEST 6: Configuration Persistence")
    print("=" * 50)

    config_file = "test_config.json"

    try:
        # Create and populate client
        client1 = GeminiMCPClient(config_file=config_file)
        client1.add_server(
            "persist1", "./example_server.py", description="Persistent server 1"
        )
        client1.add_server(
            "persist2", "./example_server.py", description="Persistent server 2"
        )
        await client1.close()
        print("✓ Saved 2 servers to configuration")

        # Create new client and load
        client2 = GeminiMCPClient(config_file=config_file)
        servers = client2.list_servers()
        print(f"✓ Loaded servers: {servers}")

        for server_name in servers:
            config = client2.servers[server_name]
            print(f"  - {server_name}: {config.description}")

        await client2.close()

        # Clean up
        import os

        if os.path.exists(config_file):
            os.remove(config_file)
            print("✓ Cleaned up test configuration file")

    except Exception as e:
        print(f"✗ Error: {e}")


async def main():
    """Run all tests"""
    print(
        """
╔════════════════════════════════════════════╗
║   Gemini MCP Client - Test Suite           ║
║   Running comprehensive tests...           ║
╚════════════════════════════════════════════╝
    """
    )

    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠ Warning: GEMINI_API_KEY not set")
        print("Some tests will be skipped\n")

        # Run non-API tests
        await test_server_management()
        await test_error_handling()
        await test_configuration_persistence()
    else:
        # Run all tests
        await test_basic_chat()
        await test_conversation_history()
        await test_server_management()
        await test_tool_discovery()
        await test_error_handling()
        await test_configuration_persistence()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
