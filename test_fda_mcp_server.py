# test_fda_server.py
import asyncio
from fda_mcp_server import FDAMCPServer

async def test_server():
    server = FDAMCPServer()
    
    # Test the search function directly
    result = await server._search_drug_events({"drug_name": "aspirin", "limit": 5})
    print("Drug events result:", result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_server())