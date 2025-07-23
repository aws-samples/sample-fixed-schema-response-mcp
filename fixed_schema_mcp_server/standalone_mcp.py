#!/usr/bin/env python3
"""
Standalone MCP server that runs both the HTTP server and the MCP wrapper.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import argparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("standalone_mcp.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_http_server(config_path, log_level):
    """
    Run the HTTP server.
    
    Args:
        config_path: Path to the configuration file
        log_level: Logging level
    """
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set up the command
    cmd = [
        sys.executable,
        os.path.join(current_dir, "run_server.py"),
        "--config", config_path,
        "--log-level", log_level
    ]
    
    # Run the command
    logger.info(f"Starting HTTP server: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Wait for the server to start
    await asyncio.sleep(2)
    
    # Check if the process is still running
    if process.returncode is not None:
        # Process exited, get the output
        stdout, stderr = await process.communicate()
        logger.error(f"HTTP server failed to start. Exit code: {process.returncode}")
        logger.error(f"HTTP server output: {stdout.decode('utf-8')}")
        logger.error(f"HTTP server error: {stderr.decode('utf-8')}")
        return None
    
    logger.info("HTTP server started")
    return process

async def run_mcp_wrapper(http_port, log_level):
    """
    Run the MCP wrapper.
    
    Args:
        http_port: HTTP server port
        log_level: Logging level
    """
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set up the command
    cmd = [
        sys.executable,
        os.path.join(current_dir, "mcp_wrapper.py"),
        "--port", str(http_port),
        "--log-level", log_level
    ]
    
    # Run the command
    logger.info(f"Starting MCP wrapper: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    logger.info("MCP wrapper started")
    return process

async def main():
    """Run the standalone MCP server."""
    parser = argparse.ArgumentParser(description="Standalone MCP server")
    parser.add_argument("--config", type=str, default="test_config/config.json", help="Path to the configuration file")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(args.log_level.upper())
    
    # Get the HTTP port from the config
    import json
    with open(args.config, 'r') as f:
        config = json.load(f)
    http_port = config.get("server", {}).get("port", 8081)
    
    # Start the HTTP server
    http_process = await run_http_server(args.config, args.log_level)
    if http_process is None:
        return 1
    
    # Start the MCP wrapper
    mcp_process = await run_mcp_wrapper(http_port, args.log_level)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(http_process, mcp_process))
        )
    
    # Wait for the processes to exit
    try:
        # Connect the MCP wrapper's stdout to our stdout
        while True:
            line = await mcp_process.stdout.readline()
            if not line:
                break
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
    except asyncio.CancelledError:
        pass
    finally:
        # Make sure we clean up
        await shutdown(http_process, mcp_process)
    
    return 0

async def shutdown(http_process, mcp_process):
    """
    Shut down the processes.
    
    Args:
        http_process: The HTTP server process
        mcp_process: The MCP wrapper process
    """
    logger.info("Shutting down...")
    
    # Terminate the MCP wrapper
    if mcp_process and mcp_process.returncode is None:
        logger.info("Terminating MCP wrapper")
        mcp_process.terminate()
        try:
            await asyncio.wait_for(mcp_process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("MCP wrapper did not terminate, killing")
            mcp_process.kill()
    
    # Terminate the HTTP server
    if http_process and http_process.returncode is None:
        logger.info("Terminating HTTP server")
        http_process.terminate()
        try:
            await asyncio.wait_for(http_process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("HTTP server did not terminate, killing")
            http_process.kill()
    
    logger.info("Shutdown complete")

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))