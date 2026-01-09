# Deployment Guide: Schema Transform MCP Server on AWS ECS Fargate

This guide covers deploying the MCP server to AWS and configuring Kiro to use it.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm
- Docker installed and running
- AWS CDK CLI (`npm install -g aws-cdk`)

## Step 1: Deploy to AWS

```bash
# Navigate to CDK directory
cd cdk

# Install dependencies
npm install

# Bootstrap CDK (first time only, per account/region)
cdk bootstrap

# Synthesize and validate (recommended before deploy)
cdk synth

# Deploy the stack
cdk deploy
```

> **Tip**: Prefer `cdk synth` over `npm run build` or `tsc` for validation. It automatically compiles TypeScript, validates constructs, and provides better error messages.

### Optional: Customize Deployment

Set environment variables before deploying:

```bash
# Use existing VPC
export EXISTING_VPC_ID=vpc-xxxxxxxx

# Adjust resources
export TASK_CPU=512
export TASK_MEMORY=1024
export DESIRED_COUNT=2

# Configure Bedrock region
export BEDROCK_REGION=us-west-2

# Create secrets for alternative providers
export CREATE_OPENAI_SECRET=true
export CREATE_ANTHROPIC_SECRET=true

# Deploy with custom settings
cdk deploy
```

## Step 2: Get the CloudFront Endpoint

After deployment, note the outputs:

```
Outputs:
McpFargateStack.CloudFrontUrl = https://dxxxxxxxxxx.cloudfront.net
McpFargateStack.McpEndpoint = https://dxxxxxxxxxx.cloudfront.net/mcp
McpFargateStack.EcrRepositoryUri = xxxxxxxxxxxx.dkr.ecr.us-west-2.amazonaws.com/mcpfargatestack-mcp-server
McpFargateStack.LogGroupName = /ecs/McpFargateStack/mcp-server
```

Test the MCP endpoint:

```bash
curl https://<CloudFrontDnsName>/mcp
```

## Step 3: Configure Kiro MCP Client

The MCP server uses **Streamable HTTP** transport, which is the modern standard for remote MCP servers.

Add to your Kiro MCP config (`.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "schema-transform": {
      "url": "http://<CloudFrontDnsName>/mcp",
      "disabled": false,
      "autoApprove": [
        "list_available_schemas"
      ]
    }
  }
}
```

Replace `<CloudFrontDnsName>` with the actual ALB DNS name from the deployment output.

### Local Development

For local development, run the MCP server with stdio transport:

```json
{
  "mcpServers": {
    "schema-transform": {
      "command": "uv",
      "args": ["run", "fastmcp_server.py"],
      "cwd": "${workspaceFolder}/fixed_schema_mcp_server",
      "disabled": false,
      "autoApprove": [
        "list_available_schemas"
      ]
    }
  }
}
```

## Step 4: Verify Connection

In Kiro, test the MCP tools:

1. Open the MCP Server view in Kiro
2. Check that `schema-transform` server is connected
3. Try calling `list_available_schemas` to verify

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Kiro IDE   │───▶│ CloudFront  │───▶│     ALB     │───▶│ ECS Fargate │
│ (MCP Client)│    │  (HTTPS)    │    │   (HTTP)    │    │ (MCP Server)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
       Streamable HTTP (POST /mcp)                              │
                                                                ▼
                                                        ┌─────────────┐
                                                        │   Amazon    │
                                                        │   Bedrock   │
                                                        └─────────────┘
```

## Updating the Deployment

To update the MCP server code:

```bash
cd cdk

# Validate changes first
cdk synth

# Compare with deployed stack
cdk diff

# Deploy updates
cdk deploy
```

CDK automatically rebuilds the Docker image and deploys the new version.

## Cleanup

To remove all resources:

```bash
cd cdk
cdk destroy
```

## Troubleshooting

### Check Container Logs

```bash
aws logs tail /ecs/McpFargateStack/mcp-server --follow
```

### Check ECS Service Status

```bash
aws ecs describe-services \
  --cluster McpFargateStack-cluster \
  --services McpFargateStack-service
```

### Health Check Failing

1. Verify the container is running: `aws ecs list-tasks --cluster McpFargateStack-cluster`
2. Check container logs for errors
3. Ensure port 8000 is exposed and FastMCP is running with streamable-http transport

### Bedrock Access Issues

Ensure the ECS task role has `bedrock:InvokeModel` permissions and the model is available in your region.

### Connection Issues from Kiro

1. Verify the ALB DNS name is correct
2. Check that the ALB security group allows inbound traffic on port 80
3. Ensure the MCP endpoint responds: `curl http://<CloudFrontDnsName>/mcp`
