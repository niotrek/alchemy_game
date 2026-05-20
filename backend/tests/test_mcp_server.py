from apothecaria.mcp.server import mcp


async def test_server_registers_the_four_store_tools():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"list_store", "get_balance", "list_inventory", "buy_ingredient"}
