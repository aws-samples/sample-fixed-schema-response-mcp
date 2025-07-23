#!/usr/bin/env python3
"""
Main entry point for the Fixed Schema Response MCP Server.
"""

import argparse
import asyncio
import logging
import os
import sys

from fixed_schema_mcp_server.core.server import MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_server(config_path: str, log_level: str):
    """
    Run the MCP server.
    
    Args:
        config_path: Path to the configuration file
        log_level: Logging level
    """
    # Set log level
    logging.getLogger().setLevel(log_level.upper())
    
    # Create and start the server
    try:
        server = MCPServer(config_path)
        await server.start()
        
        # Keep the server running until stopped
        while server.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        if server and server.is_running:
            await server.stop()
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the Fixed Schema Response MCP Server")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the configuration file")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Get config path from arguments or environment variable
    config_path = os.environ.get("FIXED_SCHEMA_MCP_CONFIG_PATH", args.config)
    
    # Get log level from arguments or environment variable
    log_level = os.environ.get("FIXED_SCHEMA_MCP_LOG_LEVEL", args.log_level).upper()
    
    # Run the server
    asyncio.run(run_server(config_path, log_level))

if __name__ == "__main__":
    main()