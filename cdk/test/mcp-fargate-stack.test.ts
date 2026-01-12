import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { McpFargateStack, McpFargateStackProps, DEFAULT_STACK_CONFIG } from '../lib/mcp-fargate-stack';

/**
 * Unit tests for the MCP Fargate Stack.
 * 
 * These tests verify individual CDK constructs produce correct CloudFormation resources.
 * Tests are organized by component: VPC, ECS, IAM, etc.
 */

describe('McpFargateStack', () => {
  // ============================================
  // VPC Configuration Tests
  // Requirements: 1.1, 1.2
  // ============================================
  describe('VPC Configuration', () => {
    test('creates new VPC when no existingVpcId is provided', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - VPC should be created
      // Requirements: 1.2 - Create VPC with public and private subnets across at least 2 AZs
      template.resourceCountIs('AWS::EC2::VPC', 1);
      
      // Verify VPC has proper CIDR configuration
      template.hasResourceProperties('AWS::EC2::VPC', {
        EnableDnsHostnames: true,
        EnableDnsSupport: true,
      });
    });

    test('creates public and private subnets in new VPC', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        vpcMaxAzs: 2,
      });
      const template = Template.fromStack(stack);

      // Assert - Should have subnets (2 public + 2 private = 4 total for 2 AZs)
      // Requirements: 1.2 - Create VPC with public and private subnets
      template.resourceCountIs('AWS::EC2::Subnet', 4);
    });

    test('creates NAT gateway for private subnet internet access', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        natGateways: 1,
      });
      const template = Template.fromStack(stack);

      // Assert - NAT Gateway should be created
      // Requirements: 1.3 - Configure NAT gateways in public subnets
      template.resourceCountIs('AWS::EC2::NatGateway', 1);
    });

    test('creates Internet Gateway for public subnet access', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Internet Gateway should be created
      template.resourceCountIs('AWS::EC2::InternetGateway', 1);
    });

    test('respects custom vpcMaxAzs configuration', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        vpcMaxAzs: 3,
      });
      const template = Template.fromStack(stack);

      // Assert - Should have 6 subnets (3 public + 3 private for 3 AZs)
      template.resourceCountIs('AWS::EC2::Subnet', 6);
    });

    test('respects custom natGateways configuration', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        natGateways: 2,
        vpcMaxAzs: 2,
      });
      const template = Template.fromStack(stack);

      // Assert - Should have 2 NAT Gateways
      template.resourceCountIs('AWS::EC2::NatGateway', 2);
    });
  });


  // ============================================
  // ECS Configuration Tests
  // Requirements: 3.1, 3.2, 3.3
  // ============================================
  describe('ECS Configuration', () => {
    test('creates ECS cluster with Fargate capacity provider', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - ECS Cluster should be created
      // Requirements: 3.1 - Create ECS cluster with Fargate capacity providers
      template.resourceCountIs('AWS::ECS::Cluster', 1);
      
      // Verify cluster has container insights enabled
      template.hasResourceProperties('AWS::ECS::Cluster', {
        ClusterSettings: Match.arrayWith([
          Match.objectLike({
            Name: 'containerInsights',
            Value: 'enabled',
          }),
        ]),
      });
    });

    test('creates task definition with default CPU and memory', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Task definition should have default CPU/memory
      // Requirements: 3.2 - Define task definition with appropriate CPU and memory allocation
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Cpu: String(DEFAULT_STACK_CONFIG.cpu),
        Memory: String(DEFAULT_STACK_CONFIG.memoryMiB),
        RequiresCompatibilities: ['FARGATE'],
        NetworkMode: 'awsvpc',
      });
    });

    test('creates task definition with custom CPU and memory', () => {
      // Arrange
      const app = new cdk.App();
      const customCpu = 1024;
      const customMemory = 2048;
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        cpu: customCpu,
        memoryMiB: customMemory,
      });
      const template = Template.fromStack(stack);

      // Assert - Task definition should have custom CPU/memory
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Cpu: String(customCpu),
        Memory: String(customMemory),
      });
    });

    test('creates Fargate service with default desired count of 2', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Service should have desired count of 2 for high availability
      // Requirements: 3.3 - Run at least 2 tasks for high availability
      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: DEFAULT_STACK_CONFIG.desiredCount,
        LaunchType: 'FARGATE',
      });
    });

    test('creates Fargate service with custom desired count', () => {
      // Arrange
      const app = new cdk.App();
      const customDesiredCount = 5;
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        desiredCount: customDesiredCount,
      });
      const template = Template.fromStack(stack);

      // Assert - Service should have custom desired count
      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: customDesiredCount,
      });
    });

    test('configures circuit breaker for automatic rollback', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Service should have circuit breaker enabled
      // Requirements: 3.4 - Automatically replace unhealthy tasks
      template.hasResourceProperties('AWS::ECS::Service', {
        DeploymentConfiguration: Match.objectLike({
          DeploymentCircuitBreaker: {
            Enable: true,
            Rollback: true,
          },
        }),
      });
    });

    test('task definition configures CloudWatch logging', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Container should have awslogs driver configured
      // Requirements: 3.5 - Configure container logging to CloudWatch Logs
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            LogConfiguration: {
              LogDriver: 'awslogs',
              Options: Match.objectLike({
                'awslogs-stream-prefix': 'mcp-server',
              }),
            },
          }),
        ]),
      });
    });

    test('task definition includes environment variables for Bedrock', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
        bedrockRegion: 'us-west-2',
      });
      const template = Template.fromStack(stack);

      // Assert - Container should have AWS_REGION and LOG_LEVEL environment variables
      // Note: BEDROCK_MODEL_ID is configured in config.json, not via environment variables
      // Requirements: 8.2 - Configure AWS region for Bedrock access
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              { Name: 'AWS_REGION', Value: 'us-west-2' },
              { Name: 'LOG_LEVEL', Value: 'INFO' },
            ]),
          }),
        ]),
      });
    });
  });


  // ============================================
  // IAM Roles Tests
  // Requirements: 5.1, 5.2, 5.3
  // ============================================
  describe('IAM Roles', () => {
    test('creates task execution role with ECR pull permissions', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Execution role should have ECR permissions
      // Requirements: 5.1 - Create IAM task execution role for ECS to pull images
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'ecr:GetAuthorizationToken',
              Effect: 'Allow',
            }),
          ]),
        },
      });

      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'ecr:BatchCheckLayerAvailability',
                'ecr:GetDownloadUrlForLayer',
                'ecr:BatchGetImage',
              ]),
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });

    test('creates task execution role with CloudWatch Logs permissions', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Execution role should have CloudWatch Logs permissions
      // Requirements: 5.1 - Create IAM task execution role for ECS to write logs
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'logs:CreateLogStream',
                'logs:PutLogEvents',
              ]),
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });

    test('creates task execution role with Secrets Manager read permissions', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Execution role should have Secrets Manager read permissions
      // Requirements: 5.1 - Create IAM task execution role for ECS to read secrets
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'secretsmanager:GetSecretValue',
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });

    test('creates task role with Bedrock InvokeModel permissions', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Task role should have Bedrock permissions
      // Requirements: 5.2, 5.3 - Create IAM task role with Bedrock InvokeModel permissions
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
              ]),
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });

    test('task role Bedrock permissions are scoped to foundation models', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Bedrock permissions should be scoped to foundation models
      // Requirements: 5.5 - Follow principle of least privilege
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
              ]),
              Effect: 'Allow',
              Resource: Match.stringLikeRegexp('arn:aws:bedrock:.*::foundation-model/\\*'),
            }),
          ]),
        },
      });
    });

    test('task role has Secrets Manager read permissions', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Task role should have Secrets Manager read permissions
      // Requirements: 5.4 - IAM_Task_Role SHALL have permissions to read secrets
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'secretsmanager:GetSecretValue',
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });

    test('execution role is assumed by ECS tasks service principal', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Execution role should be assumable by ECS tasks
      template.hasResourceProperties('AWS::IAM::Role', {
        AssumeRolePolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'sts:AssumeRole',
              Effect: 'Allow',
              Principal: {
                Service: 'ecs-tasks.amazonaws.com',
              },
            }),
          ]),
        },
      });
    });

    test('task definition references both execution and task roles', () => {
      // Arrange
      const app = new cdk.App();
      
      // Act
      const stack = new McpFargateStack(app, 'TestStack', {
        env: { account: '123456789012', region: 'us-east-1' },
      });
      const template = Template.fromStack(stack);

      // Assert - Task definition should reference both roles
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ExecutionRoleArn: Match.anyValue(),
        TaskRoleArn: Match.anyValue(),
      });
    });
  });

  // Close the main describe block
});
