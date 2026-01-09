#!/usr/bin/env node
/**
 * CDK App Entry Point for MCP Fargate Stack
 * 
 * This file instantiates the McpFargateStack with configurable parameters.
 * All configuration can be overridden via environment variables.
 * 
 * Environment Variables:
 * - CDK_DEFAULT_ACCOUNT: AWS account ID (auto-detected if not set)
 * - CDK_DEFAULT_REGION: AWS region (auto-detected if not set)
 * 
 * VPC Configuration:
 * - EXISTING_VPC_ID: ID of existing VPC to use (optional, creates new VPC if not set)
 * - VPC_MAX_AZS: Maximum availability zones for new VPC (default: 2)
 * - NAT_GATEWAYS: Number of NAT gateways for new VPC (default: 1)
 * 
 * ECS Configuration:
 * - TASK_CPU: CPU units for Fargate task (default: 256)
 * - TASK_MEMORY: Memory in MiB for Fargate task (default: 512)
 * - DESIRED_COUNT: Number of tasks to run (default: 2)
 * 
 * Container Configuration:
 * - CONTAINER_PORT: Port the container listens on (default: 8000)
 * - HEALTH_CHECK_PATH: Health check endpoint path (default: /health)
 * 
 * Bedrock Configuration:
 * - BEDROCK_REGION: AWS region for Bedrock API calls (default: stack region)
 * - BEDROCK_MODEL_ID: Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)
 * 
 * Secrets Configuration:
 * - CREATE_OPENAI_SECRET: Set to 'true' to create OpenAI API key secret
 * - CREATE_ANTHROPIC_SECRET: Set to 'true' to create Anthropic API key secret
 * 
 * Requirements: 9.1 - Accept parameters for CPU, memory, and desired task count
 */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { McpFargateStack } from '../lib/mcp-fargate-stack';

const app = new cdk.App();

/**
 * Helper function to parse integer environment variables with defaults.
 * Returns undefined if the environment variable is not set and no default is provided.
 */
function parseIntEnv(envVar: string | undefined, defaultValue: number): number {
  if (envVar === undefined || envVar === '') {
    return defaultValue;
  }
  const parsed = parseInt(envVar, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Helper function to parse boolean environment variables.
 * Returns true only if the value is exactly 'true' (case-insensitive).
 */
function parseBoolEnv(envVar: string | undefined): boolean {
  return envVar?.toLowerCase() === 'true';
}

/**
 * Helper function to get optional string environment variable.
 * Returns undefined if the environment variable is not set or empty.
 */
function getOptionalEnv(envVar: string | undefined): string | undefined {
  return envVar && envVar.trim() !== '' ? envVar.trim() : undefined;
}

// Create the MCP Fargate stack with default configuration
// All parameters can be overridden via environment variables
new McpFargateStack(app, 'McpFargateStack', {
  // AWS Environment Configuration
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  
  // Stack metadata
  description: 'Fixed Schema MCP Server deployed on AWS ECS Fargate',
  
  // VPC Configuration
  // If EXISTING_VPC_ID is set, use that VPC; otherwise create a new one
  existingVpcId: getOptionalEnv(process.env.EXISTING_VPC_ID),
  vpcMaxAzs: parseIntEnv(process.env.VPC_MAX_AZS, 2),
  natGateways: parseIntEnv(process.env.NAT_GATEWAYS, 1),
  
  // ECS Configuration - Requirements: 9.1
  cpu: parseIntEnv(process.env.TASK_CPU, 256),
  memoryMiB: parseIntEnv(process.env.TASK_MEMORY, 512),
  desiredCount: parseIntEnv(process.env.DESIRED_COUNT, 1),
  
  // Container Configuration
  containerPort: parseIntEnv(process.env.CONTAINER_PORT, 8000),
  healthCheckPath: process.env.HEALTH_CHECK_PATH || '/health',
  
  // Bedrock Configuration
  bedrockRegion: getOptionalEnv(process.env.BEDROCK_REGION),
  bedrockModelId: process.env.BEDROCK_MODEL_ID || 'anthropic.claude-3-sonnet-20240229-v1:0',
  
  // Secrets Configuration
  createOpenAiSecret: parseBoolEnv(process.env.CREATE_OPENAI_SECRET),
  createAnthropicSecret: parseBoolEnv(process.env.CREATE_ANTHROPIC_SECRET),
});

app.synth();
