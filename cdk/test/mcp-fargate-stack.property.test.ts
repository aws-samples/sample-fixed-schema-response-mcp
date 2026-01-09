import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as fc from 'fast-check';
import { McpFargateStack, McpFargateStackProps, DEFAULT_STACK_CONFIG } from '../lib/mcp-fargate-stack';

/**
 * Property-based tests for the MCP Fargate Stack.
 * 
 * These tests verify universal properties across all valid configurations
 * using fast-check for property-based testing.
 * 
 * Feature: mcp-ecs-fargate-deployment
 */

// ============================================
// Arbitraries for generating valid stack configurations
// ============================================

// Valid Fargate CPU values
const cpuArbitrary = fc.constantFrom(256, 512, 1024, 2048, 4096);

// Valid memory values (must be compatible with CPU)
const memoryArbitrary = fc.constantFrom(512, 1024, 2048, 4096, 8192);

// Desired count between 1 and 10
const desiredCountArbitrary = fc.integer({ min: 1, max: 10 });

// VPC max AZs between 2 and 3
const vpcMaxAzsArbitrary = fc.integer({ min: 2, max: 3 });

// NAT gateways between 1 and 3
const natGatewaysArbitrary = fc.integer({ min: 1, max: 3 });

// Container port (common ports)
const containerPortArbitrary = fc.constantFrom(8000, 8080, 3000, 5000);

// Health check path
const healthCheckPathArbitrary = fc.constantFrom('/health', '/healthz', '/status', '/');

// Bedrock model IDs
const bedrockModelIdArbitrary = fc.constantFrom(
  'anthropic.claude-3-sonnet-20240229-v1:0',
  'anthropic.claude-3-haiku-20240307-v1:0',
  'amazon.titan-text-express-v1'
);

// Boolean for secrets creation
const booleanArbitrary = fc.boolean();

// Combined arbitrary for stack props (without existingVpcId - new VPC path)
const newVpcStackPropsArbitrary = fc.record({
  cpu: cpuArbitrary,
  memoryMiB: memoryArbitrary,
  desiredCount: desiredCountArbitrary,
  vpcMaxAzs: vpcMaxAzsArbitrary,
  natGateways: natGatewaysArbitrary,
  containerPort: containerPortArbitrary,
  healthCheckPath: healthCheckPathArbitrary,
  bedrockModelId: bedrockModelIdArbitrary,
  createOpenAiSecret: booleanArbitrary,
  createAnthropicSecret: booleanArbitrary,
});

// Helper function to create a stack with given props
function createStackWithProps(props: Partial<McpFargateStackProps>, stackId: string = 'TestStack'): {
  stack: McpFargateStack;
  template: Template;
} {
  const app = new cdk.App();
  const stack = new McpFargateStack(app, stackId, {
    env: { account: '123456789012', region: 'us-east-1' },
    ...props,
  });
  const template = Template.fromStack(stack);
  return { stack, template };
}

// Number of iterations for property tests (reduced for faster execution)
const NUM_RUNS = 10;

describe('McpFargateStack Property Tests', () => {

  // ============================================
  // Property 1: VPC Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 1: VPC Configuration
  // Validates: Requirements 1.1, 1.2, 1.4
  // ============================================
  describe('Property 1: VPC Configuration', () => {
    it('should create VPC with at least 2 AZs, public subnets with IGW, and private subnets with NAT when no existingVpcId provided', () => {
      fc.assert(
        fc.property(
          fc.record({
            vpcMaxAzs: vpcMaxAzsArbitrary,
            // NAT gateways are capped at the number of AZs
            natGateways: fc.integer({ min: 1, max: 2 }),
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify VPC is created
            template.resourceCountIs('AWS::EC2::VPC', 1);

            // Verify subnets are created (public + private per AZ)
            const expectedSubnets = config.vpcMaxAzs * 2;
            template.resourceCountIs('AWS::EC2::Subnet', expectedSubnets);

            // Verify Internet Gateway is created for public subnets
            template.resourceCountIs('AWS::EC2::InternetGateway', 1);

            // Verify NAT Gateways are created (capped at number of AZs)
            const expectedNatGateways = Math.min(config.natGateways, config.vpcMaxAzs);
            template.resourceCountIs('AWS::EC2::NatGateway', expectedNatGateways);

            // Verify VPC has DNS support enabled
            template.hasResourceProperties('AWS::EC2::VPC', {
              EnableDnsHostnames: true,
              EnableDnsSupport: true,
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 2: Security Group Restrictions
  // Feature: mcp-ecs-fargate-deployment, Property 2: Security Group Restrictions
  // Validates: Requirements 1.3
  // ============================================
  describe('Property 2: Security Group Restrictions', () => {
    it('should only allow traffic on required ports (80 for ALB, container port for internal)', () => {
      fc.assert(
        fc.property(
          fc.record({
            containerPort: containerPortArbitrary,
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Get all security group ingress rules
            const securityGroups = template.findResources('AWS::EC2::SecurityGroup');
            
            // Verify ALB security group allows port 80
            template.hasResourceProperties('AWS::EC2::SecurityGroup', {
              SecurityGroupIngress: Match.arrayWith([
                Match.objectLike({
                  FromPort: 80,
                  ToPort: 80,
                  IpProtocol: 'tcp',
                }),
              ]),
            });

            // Verify no security group has unrestricted access (0.0.0.0/0) to all ports
            // ALB can have 0.0.0.0/0 on port 80, but not on all ports
            for (const [, sg] of Object.entries(securityGroups)) {
              const sgProps = (sg as any).Properties;
              if (sgProps.SecurityGroupIngress) {
                for (const rule of sgProps.SecurityGroupIngress) {
                  // If CidrIp is 0.0.0.0/0, it should only be for specific ports (80)
                  if (rule.CidrIp === '0.0.0.0/0') {
                    expect(rule.FromPort).toBeDefined();
                    expect(rule.ToPort).toBeDefined();
                    // Should not allow all ports (FromPort: 0, ToPort: 65535)
                    expect(rule.FromPort === 0 && rule.ToPort === 65535).toBe(false);
                  }
                }
              }
            }

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 3: ECR Repository Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 3: ECR Repository Configuration
  // Validates: Requirements 2.1, 2.2, 2.3
  // ============================================
  describe('Property 3: ECR Repository Configuration', () => {
    it('should create ECR repository with image scanning enabled and lifecycle policy', () => {
      fc.assert(
        fc.property(
          newVpcStackPropsArbitrary,
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify ECR repository is created
            template.resourceCountIs('AWS::ECR::Repository', 1);

            // Verify image scanning is enabled
            template.hasResourceProperties('AWS::ECR::Repository', {
              ImageScanningConfiguration: {
                ScanOnPush: true,
              },
            });

            // Verify lifecycle policy exists (retains last 10 images)
            // The actual policy uses countNumber:10, not maxImageCount
            template.hasResourceProperties('AWS::ECR::Repository', {
              LifecyclePolicy: Match.objectLike({
                LifecyclePolicyText: Match.stringLikeRegexp('.*countNumber.*10.*'),
              }),
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 4: ECS Fargate Service Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 4: ECS Fargate Service Configuration
  // Validates: Requirements 3.1, 3.2, 3.3
  // ============================================
  describe('Property 4: ECS Fargate Service Configuration', () => {
    it('should create ECS cluster, task definition with specified CPU/memory, and Fargate service with configured task count', () => {
      fc.assert(
        fc.property(
          fc.record({
            cpu: cpuArbitrary,
            memoryMiB: memoryArbitrary,
            desiredCount: desiredCountArbitrary,
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify ECS cluster is created
            template.resourceCountIs('AWS::ECS::Cluster', 1);

            // Verify task definition has correct CPU and memory
            template.hasResourceProperties('AWS::ECS::TaskDefinition', {
              Cpu: String(config.cpu),
              Memory: String(config.memoryMiB),
              RequiresCompatibilities: ['FARGATE'],
              NetworkMode: 'awsvpc',
            });

            // Verify Fargate service has correct desired count
            template.hasResourceProperties('AWS::ECS::Service', {
              DesiredCount: config.desiredCount,
              LaunchType: 'FARGATE',
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 5: CloudWatch Logging Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 5: CloudWatch Logging Configuration
  // Validates: Requirements 3.5, 7.1, 7.2, 7.3
  // ============================================
  describe('Property 5: CloudWatch Logging Configuration', () => {
    it('should configure awslogs driver pointing to CloudWatch log group with 30-day retention', () => {
      fc.assert(
        fc.property(
          newVpcStackPropsArbitrary,
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify CloudWatch log group is created
            template.resourceCountIs('AWS::Logs::LogGroup', 1);

            // Verify log retention is 30 days
            template.hasResourceProperties('AWS::Logs::LogGroup', {
              RetentionInDays: 30,
            });

            // Verify task definition uses awslogs driver
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

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 6: ALB Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 6: ALB Configuration
  // Validates: Requirements 4.1, 4.2, 4.3
  // ============================================
  describe('Property 6: ALB Configuration', () => {
    it('should create internet-facing ALB in public subnets with listener on port 80 and health check', () => {
      fc.assert(
        fc.property(
          fc.record({
            healthCheckPath: healthCheckPathArbitrary,
            containerPort: containerPortArbitrary,
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify ALB is created and internet-facing
            template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
              Scheme: 'internet-facing',
              Type: 'application',
            });

            // Verify HTTP listener on port 80
            template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
              Port: 80,
              Protocol: 'HTTP',
            });

            // Verify target group has health check configured
            template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
              HealthCheckPath: config.healthCheckPath,
              HealthCheckProtocol: 'HTTP',
              Port: config.containerPort,
              Protocol: 'HTTP',
              TargetType: 'ip',
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 7: IAM Least Privilege
  // Feature: mcp-ecs-fargate-deployment, Property 7: IAM Least Privilege
  // Validates: Requirements 5.1, 5.2, 5.3, 5.4
  // ============================================
  describe('Property 7: IAM Least Privilege', () => {
    it('should create execution role with only ECR, CloudWatch, Secrets permissions and task role with only Bedrock, Secrets permissions', () => {
      fc.assert(
        fc.property(
          newVpcStackPropsArbitrary,
          (config) => {
            const { template } = createStackWithProps(config);

            // Get all IAM policies
            const policies = template.findResources('AWS::IAM::Policy');

            // Track which permissions we find
            let hasEcrPull = false;
            let hasCloudWatchLogs = false;
            let hasSecretsRead = false;
            let hasBedrockInvoke = false;

            for (const [, policy] of Object.entries(policies)) {
              const statements = (policy as any).Properties?.PolicyDocument?.Statement || [];
              for (const statement of statements) {
                const actions = Array.isArray(statement.Action) ? statement.Action : [statement.Action];
                
                // Check for ECR permissions
                if (actions.some((a: string) => a.includes('ecr:'))) {
                  hasEcrPull = true;
                  // Verify ECR actions are scoped (not ecr:*)
                  expect(actions).not.toContain('ecr:*');
                }

                // Check for CloudWatch Logs permissions
                if (actions.some((a: string) => a.includes('logs:'))) {
                  hasCloudWatchLogs = true;
                  // Verify logs actions are scoped
                  expect(actions).not.toContain('logs:*');
                }

                // Check for Secrets Manager permissions
                if (actions.some((a: string) => a.includes('secretsmanager:'))) {
                  hasSecretsRead = true;
                  // Verify only read-related actions are allowed (GetSecretValue and DescribeSecret)
                  const smActions = actions.filter((a: string) => a.includes('secretsmanager:'));
                  expect(smActions.every((a: string) => 
                    a === 'secretsmanager:GetSecretValue' || a === 'secretsmanager:DescribeSecret'
                  )).toBe(true);
                }

                // Check for Bedrock permissions
                if (actions.some((a: string) => a.includes('bedrock:'))) {
                  hasBedrockInvoke = true;
                  // Verify only InvokeModel actions are allowed
                  const brActions = actions.filter((a: string) => a.includes('bedrock:'));
                  expect(brActions.every((a: string) => 
                    a === 'bedrock:InvokeModel' || a === 'bedrock:InvokeModelWithResponseStream'
                  )).toBe(true);
                }

                // Verify no admin or wildcard permissions
                expect(actions).not.toContain('*');
                expect(actions).not.toContain('iam:*');
                expect(actions).not.toContain('s3:*');
              }
            }

            // Verify all required permissions exist
            expect(hasEcrPull).toBe(true);
            expect(hasCloudWatchLogs).toBe(true);
            expect(hasSecretsRead).toBe(true);
            expect(hasBedrockInvoke).toBe(true);

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 8: Secrets Management
  // Feature: mcp-ecs-fargate-deployment, Property 8: Secrets Management
  // Validates: Requirements 6.1, 6.2, 6.4
  // ============================================
  describe('Property 8: Secrets Management', () => {
    it('should create Secrets Manager secrets when enabled and reference them in container without plain text', () => {
      fc.assert(
        fc.property(
          fc.record({
            createOpenAiSecret: fc.constant(true),
            createAnthropicSecret: fc.constant(true),
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify secrets are created
            template.resourceCountIs('AWS::SecretsManager::Secret', 2);

            // Verify container definition references secrets (not plain text env vars)
            const taskDefs = template.findResources('AWS::ECS::TaskDefinition');
            for (const [, taskDef] of Object.entries(taskDefs)) {
              const containerDefs = (taskDef as any).Properties?.ContainerDefinitions || [];
              for (const container of containerDefs) {
                // Check that secrets are referenced via Secrets property
                if (container.Secrets) {
                  for (const secret of container.Secrets) {
                    // Verify secret references use ValueFrom (not plain text)
                    expect(secret.ValueFrom).toBeDefined();
                    expect(secret.Name).toBeDefined();
                  }
                }

                // Verify no API keys in plain text environment variables
                if (container.Environment) {
                  for (const env of container.Environment) {
                    expect(env.Name).not.toBe('OPENAI_API_KEY');
                    expect(env.Name).not.toBe('ANTHROPIC_API_KEY');
                  }
                }
              }
            }

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });

    it('should not create secrets when disabled', () => {
      fc.assert(
        fc.property(
          fc.record({
            createOpenAiSecret: fc.constant(false),
            createAnthropicSecret: fc.constant(false),
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify no secrets are created
            template.resourceCountIs('AWS::SecretsManager::Secret', 0);

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 9: Bedrock Environment Configuration
  // Feature: mcp-ecs-fargate-deployment, Property 9: Bedrock Environment Configuration
  // Validates: Requirements 8.2, 8.4
  // ============================================
  describe('Property 9: Bedrock Environment Configuration', () => {
    it('should include AWS_REGION and BEDROCK_MODEL_ID environment variables with configured values', () => {
      fc.assert(
        fc.property(
          fc.record({
            bedrockModelId: bedrockModelIdArbitrary,
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify container has Bedrock environment variables
            template.hasResourceProperties('AWS::ECS::TaskDefinition', {
              ContainerDefinitions: Match.arrayWith([
                Match.objectLike({
                  Environment: Match.arrayWith([
                    { Name: 'BEDROCK_MODEL_ID', Value: config.bedrockModelId },
                  ]),
                }),
              ]),
            });

            // Verify AWS_REGION is set (will be us-east-1 from our test env)
            template.hasResourceProperties('AWS::ECS::TaskDefinition', {
              ContainerDefinitions: Match.arrayWith([
                Match.objectLike({
                  Environment: Match.arrayWith([
                    Match.objectLike({ Name: 'AWS_REGION' }),
                  ]),
                }),
              ]),
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 10: Stack Outputs Completeness
  // Feature: mcp-ecs-fargate-deployment, Property 10: Stack Outputs Completeness
  // Validates: Requirements 9.2, 9.3, 9.4
  // ============================================
  describe('Property 10: Stack Outputs Completeness', () => {
    it('should have CfnOutputs for ALB DNS name, ECR repository URI, and CloudWatch log group name', () => {
      fc.assert(
        fc.property(
          newVpcStackPropsArbitrary,
          (config) => {
            const { template } = createStackWithProps(config);

            // Get all outputs
            const outputs = template.findOutputs('*');

            // Verify ALB DNS name output exists
            expect(outputs).toHaveProperty('AlbDnsName');
            expect(outputs.AlbDnsName.Export?.Name).toMatch(/AlbDnsName$/);

            // Verify ECR repository URI output exists
            expect(outputs).toHaveProperty('EcrRepositoryUri');
            expect(outputs.EcrRepositoryUri.Export?.Name).toMatch(/EcrRepositoryUri$/);

            // Verify CloudWatch log group name output exists
            expect(outputs).toHaveProperty('LogGroupName');
            expect(outputs.LogGroupName.Export?.Name).toMatch(/LogGroupName$/);

            // Verify ECS cluster ARN output exists
            expect(outputs).toHaveProperty('EcsClusterArn');

            // Verify ECS service ARN output exists
            expect(outputs).toHaveProperty('EcsServiceArn');

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });
  });


  // ============================================
  // Property 11: Configuration Parameterization
  // Feature: mcp-ecs-fargate-deployment, Property 11: Configuration Parameterization
  // Validates: Requirements 9.1
  // ============================================
  describe('Property 11: Configuration Parameterization', () => {
    it('should reflect custom CPU, memory, and desiredCount values in the synthesized template', () => {
      fc.assert(
        fc.property(
          fc.record({
            cpu: cpuArbitrary,
            memoryMiB: memoryArbitrary,
            desiredCount: desiredCountArbitrary,
          }),
          (config) => {
            const { template } = createStackWithProps(config);

            // Verify task definition has exact CPU value
            template.hasResourceProperties('AWS::ECS::TaskDefinition', {
              Cpu: String(config.cpu),
            });

            // Verify task definition has exact memory value
            template.hasResourceProperties('AWS::ECS::TaskDefinition', {
              Memory: String(config.memoryMiB),
            });

            // Verify service has exact desired count
            template.hasResourceProperties('AWS::ECS::Service', {
              DesiredCount: config.desiredCount,
            });

            return true;
          }
        ),
        { numRuns: NUM_RUNS }
      );
    });

    it('should use default values when no custom configuration is provided', () => {
      const { template } = createStackWithProps({});

      // Verify default CPU
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Cpu: String(DEFAULT_STACK_CONFIG.cpu),
      });

      // Verify default memory
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Memory: String(DEFAULT_STACK_CONFIG.memoryMiB),
      });

      // Verify default desired count
      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: DEFAULT_STACK_CONFIG.desiredCount,
      });
    });
  });
});
