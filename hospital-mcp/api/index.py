"""Vercel entry point — Streamable HTTP transport for the Hospital Guardian MCP Server."""

from starlette.middleware.cors import CORSMiddleware
from hospital.server import mcp

# Create the ASGI app with Streamable HTTP transport
app = mcp.streamable_http_app()

# Add CORS middleware so platform.armoriq.ai can reach the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
