import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecr_assets from 'aws-cdk-lib/aws-ecr-assets';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as path from 'path';
import { Construct } from 'constructs';

/**
 * Configuration properties for the MCP Fargate Stack.
 * 
 * This interface defines all configurable parameters for deploying
 * the Fixed Schema MCP Server to AWS ECS Fargate.
 */
export interface McpFargateStackProps extends cdk.StackProps {
  // ============================================
  // VPC Configuration
  // ============================================
  
  /**
   * ID of an existing VPC to use.
   * If provided, the stack will use this VPC instead of creating a new one.
   * The VPC must have public and private subnets.
   */
  readonly existingVpcId?: string;

  /**
   * Maximum number of availability zones to use when creating a new VPC.
   * Only used when existingVpcId is not provided.
   * @default 2
   */
  readonly vpcMaxAzs?: number;

  /**
   * Number of NAT gateways to create when creating a new VPC.
   * Only used when existingVpcId is not provided.
   * @default 1
   */
  readonly natGateways?: number;

  // ============================================
  // ECS Configuration
  // ============================================

  /**
   * CPU units for the Fargate task.
   * Valid values: 256, 512, 1024, 2048, 4096
   * @default 256
   */
  readonly cpu?: number;

  /**
   * Memory (in MiB) for the Fargate task.
   * Valid values depend on CPU: 512-30720
   * @default 512
   */
  readonly memoryMiB?: number;

  /**
   * Desired number of tasks to run in the service.
   * @default 2
   */
  readonly desiredCount?: number;

  // ============================================
  // Container Configuration
  // ============================================

  /**
   * Port the container listens on.
   * @default 8000
   */
  readonly containerPort?: number;

  /**
   * Path for ALB health checks.
   * @default "/health"
   */
  readonly healthCheckPath?: string;

  // ============================================
  // Bedrock Configuration
  // ============================================

  /**
   * AWS region for Bedrock API calls.
   * @default - Uses the stack's region
   */
  readonly bedrockRegion?: string;

  /**
   * Bedrock model ID to use for AI inference.
   * @default "anthropic.claude-3-sonnet-20240229-v1:0"
   */
  readonly bedrockModelId?: string;

  // ============================================
  // Secrets Configuration
  // ============================================

  /**
   * Whether to create a Secrets Manager secret for OpenAI API key.
   * @default false
   */
  readonly createOpenAiSecret?: boolean;

  /**
   * Whether to create a Secrets Manager secret for Anthropic API key.
   * @default false
   */
  readonly createAnthropicSecret?: boolean;

  // ============================================
  // Docker Image Configuration
  // ============================================

  /**
   * Path to the directory containing the Dockerfile.
   * @default "../fixed_schema_mcp_server" (relative to cdk directory)
   */
  readonly dockerBuildContext?: string;
}

/**
 * Default values for stack configuration.
 */
export const DEFAULT_STACK_CONFIG = {
  vpcMaxAzs: 2,
  natGateways: 1,
  cpu: 256,
  memoryMiB: 512,
  desiredCount: 1,  // Temporarily set to 1 to debug MCP connection issues
  containerPort: 8000,
  healthCheckPath: '/health',
  bedrockModelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
  createOpenAiSecret: false,
  createAnthropicSecret: false,
  dockerBuildContext: path.join(__dirname, '../../fixed_schema_mcp_server'),
  logRetentionDays: 30,
} as const;

/**
 * CDK Stack for deploying the Fixed Schema MCP Server to AWS ECS Fargate.
 */
export class McpFargateStack extends cdk.Stack {
  /**
   * The VPC used by the stack (either existing or newly created).
   */
  public readonly vpc: ec2.IVpc;

  /**
   * The ECR repository for storing MCP server Docker images.
   */
  public readonly ecrRepository: ecr.Repository;

  /**
   * The Docker image asset that is built and pushed to ECR.
   * This is used by ECS to pull the container image.
   */
  public readonly dockerImageAsset: ecr_assets.DockerImageAsset;

  /**
   * IAM role for ECS task execution.
   * Used by ECS agent to pull images, write logs, and read secrets.
   * Requirements: 5.1
   */
  public readonly taskExecutionRole: iam.Role;

  /**
   * IAM role for the application running in the container.
   * Used to invoke Bedrock models and read secrets.
   * Requirements: 5.2, 5.3, 5.4, 8.1
   */
  public readonly taskRole: iam.Role;

  /**
   * Optional Secrets Manager secret for OpenAI API key.
   * Created only when createOpenAiSecret is true.
   * Requirements: 6.1
   */
  public readonly openAiApiKeySecret?: secretsmanager.Secret;

  /**
   * Optional Secrets Manager secret for Anthropic API key.
   * Created only when createAnthropicSecret is true.
   * Requirements: 6.1
   */
  public readonly anthropicApiKeySecret?: secretsmanager.Secret;

  /**
   * CloudWatch log group for container logs.
   * Requirements: 7.1, 7.3
   */
  public readonly logGroup: logs.LogGroup;

  /**
   * ECS cluster with Fargate capacity provider.
   * Requirements: 3.1
   */
  public readonly ecsCluster: ecs.Cluster;

  /**
   * ECS task definition for the MCP server container.
   * Requirements: 3.2, 3.5, 6.2, 7.2, 8.2, 8.4
   */
  public readonly taskDefinition: ecs.FargateTaskDefinition;

  /**
   * ECS Fargate service running the MCP server.
   * Requirements: 3.3, 3.4
   */
  public readonly fargateService: ecs.FargateService;

  /**
   * Application Load Balancer for routing traffic to the Fargate service.
   * Requirements: 4.1
   */
  public readonly alb: elbv2.ApplicationLoadBalancer;

  /**
   * Security group for the Application Load Balancer.
   * Requirements: 1.4
   */
  public readonly albSecurityGroup: ec2.SecurityGroup;

  /**
   * Target group for the Fargate service.
   * Requirements: 4.2
   */
  public readonly targetGroup: elbv2.ApplicationTargetGroup;

  /**
   * HTTP listener on port 80.
   * Requirements: 4.3
   */
  public readonly httpListener: elbv2.ApplicationListener;

  /**
   * CloudFront distribution for HTTPS access.
   * Provides free HTTPS with *.cloudfront.net domain.
   */
  public readonly cloudFrontDistribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props?: McpFargateStackProps) {
    super(scope, id, props);

    // Configure VPC - either use existing or create new
    this.vpc = this.configureVpc(props);

    // Create ECR repository for container images
    this.ecrRepository = this.createEcrRepository();

    // Build and push Docker image to ECR
    // Requirements: 2.4 - WHEN deploying the stack THEN build and push the Docker image to ECR
    this.dockerImageAsset = this.createDockerImageAsset(props);

    // Create IAM roles for ECS tasks
    // Requirements: 5.1 - Task execution role for ECS agent
    this.taskExecutionRole = this.createTaskExecutionRole();

    // Requirements: 5.2, 5.3, 5.4, 8.1 - Task role for application
    this.taskRole = this.createTaskRole(props);

    // Create optional Secrets Manager secrets for API keys
    // Requirements: 6.1 - Create Secrets Manager secrets for optional API keys
    const secrets = this.createOptionalSecrets(props);
    this.openAiApiKeySecret = secrets.openAiSecret;
    this.anthropicApiKeySecret = secrets.anthropicSecret;

    // Create CloudWatch log group for container logs
    // Requirements: 7.1 - Create CloudWatch log group for container logs
    // Requirements: 7.3 - Set log retention to 30 days
    this.logGroup = this.createLogGroup();

    // Create ECS cluster with Fargate capacity provider
    // Requirements: 3.1 - Create ECS cluster with Fargate capacity providers
    this.ecsCluster = this.createEcsCluster();

    // Create ECS task definition with container configuration
    // Requirements: 3.2, 3.5, 6.2, 7.2, 8.2, 8.4
    this.taskDefinition = this.createTaskDefinition(props);

    // Create Fargate service
    // Requirements: 3.3, 3.4
    this.fargateService = this.createFargateService(props);

    // Create Application Load Balancer
    // Requirements: 4.1, 1.4 - Create internet-facing ALB in public subnets with security group
    const albResources = this.createApplicationLoadBalancer(props);
    this.alb = albResources.alb;
    this.albSecurityGroup = albResources.securityGroup;

    // Create target group and listener
    // Requirements: 4.2, 4.3 - Configure health check, HTTP listener, and register Fargate service
    const listenerResources = this.createTargetGroupAndListener(props);
    this.targetGroup = listenerResources.targetGroup;
    this.httpListener = listenerResources.listener;

    // Create CloudFront distribution for HTTPS access
    this.cloudFrontDistribution = this.createCloudFrontDistribution();

    // Create stack outputs for key resources
    // Requirements: 9.2, 9.3, 9.4 - Output ALB DNS name, ECR repository URI, CloudWatch log group name
    this.createStackOutputs();
  }

  /**
   * Creates a CloudFront distribution for HTTPS access to the MCP server.
   * 
   * CloudFront provides:
   * - Free HTTPS with *.cloudfront.net domain
   * - Global edge caching (disabled for MCP API)
   * - DDoS protection via AWS Shield Standard
   * 
   * @returns The CloudFront distribution
   */
  private createCloudFrontDistribution(): cloudfront.Distribution {
    return new cloudfront.Distribution(this, 'McpCloudFront', {
      comment: `CloudFront distribution for ${this.stackName} MCP server`,
      defaultBehavior: {
        origin: new origins.HttpOrigin(this.alb.loadBalancerDnsName, {
          protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          httpPort: 80,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
      },
      // Enable HTTP/2 for better performance
      httpVersion: cloudfront.HttpVersion.HTTP2,
      // Price class - use only North America and Europe for lower cost
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
    });
  }

  /**
   * Creates CloudFormation outputs for key resources.
   * 
   * These outputs provide easy access to important resource information
   * after deployment, such as the ALB DNS name for accessing the service.
   * 
   * Requirements: 9.2 - Output the ALB DNS name for accessing the service
   * Requirements: 9.3 - Output the ECR repository URI for image pushes
   * Requirements: 9.4 - Output the CloudWatch log group name for log access
   */
  private createStackOutputs(): void {
    // Output ALB DNS name for accessing the service
    // Requirements: 9.2 - Output the ALB DNS name for accessing the service
    new cdk.CfnOutput(this, 'AlbDnsName', {
      value: this.alb.loadBalancerDnsName,
      description: 'DNS name of the Application Load Balancer for accessing the MCP service',
      exportName: `${this.stackName}-AlbDnsName`,
    });

    // Output ECR repository URI for image pushes
    // Requirements: 9.3 - Output the ECR repository URI for image pushes
    new cdk.CfnOutput(this, 'EcrRepositoryUri', {
      value: this.ecrRepository.repositoryUri,
      description: 'URI of the ECR repository for pushing MCP server Docker images',
      exportName: `${this.stackName}-EcrRepositoryUri`,
    });

    // Output CloudWatch log group name for log access
    // Requirements: 9.4 - Output the CloudWatch log group name for log access
    new cdk.CfnOutput(this, 'LogGroupName', {
      value: this.logGroup.logGroupName,
      description: 'Name of the CloudWatch log group for container logs',
      exportName: `${this.stackName}-LogGroupName`,
    });

    // Output ECS cluster ARN for reference
    new cdk.CfnOutput(this, 'EcsClusterArn', {
      value: this.ecsCluster.clusterArn,
      description: 'ARN of the ECS cluster running the MCP service',
      exportName: `${this.stackName}-EcsClusterArn`,
    });

    // Output ECS service ARN for reference
    new cdk.CfnOutput(this, 'EcsServiceArn', {
      value: this.fargateService.serviceArn,
      description: 'ARN of the ECS Fargate service running the MCP server',
      exportName: `${this.stackName}-EcsServiceArn`,
    });

    // Output CloudFront URL for HTTPS access
    new cdk.CfnOutput(this, 'CloudFrontUrl', {
      value: `https://${this.cloudFrontDistribution.distributionDomainName}`,
      description: 'CloudFront HTTPS URL for accessing the MCP service',
      exportName: `${this.stackName}-CloudFrontUrl`,
    });

    // Output CloudFront MCP endpoint for Kiro configuration
    new cdk.CfnOutput(this, 'McpEndpoint', {
      value: `https://${this.cloudFrontDistribution.distributionDomainName}/mcp`,
      description: 'MCP endpoint URL for Kiro configuration',
      exportName: `${this.stackName}-McpEndpoint`,
    });
  }

  /**
   * Configures the VPC for the stack.
   * 
   * If existingVpcId is provided, looks up the existing VPC.
   * Otherwise, creates a new VPC with public and private subnets.
   * 
   * @param props - Stack properties containing VPC configuration
   * @returns The configured VPC
   */
  private configureVpc(props?: McpFargateStackProps): ec2.IVpc {
    if (props?.existingVpcId) {
      // Use existing VPC - lookup by ID
      // Requirements: 1.1 - WHEN an existing VPC ID is provided THEN use that VPC
      return ec2.Vpc.fromLookup(this, 'ExistingVpc', {
        vpcId: props.existingVpcId,
      });
    }

    // Create new VPC with public and private subnets
    // Requirements: 1.2 - Create VPC with public and private subnets across at least 2 AZs
    // Requirements: 1.3 - Configure NAT gateways in public subnets
    const maxAzs = props?.vpcMaxAzs ?? DEFAULT_STACK_CONFIG.vpcMaxAzs;
    const natGateways = props?.natGateways ?? DEFAULT_STACK_CONFIG.natGateways;

    return new ec2.Vpc(this, 'McpVpc', {
      maxAzs: maxAzs,
      natGateways: natGateways,
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });
  }

  /**
   * Creates an ECR repository for storing MCP server Docker images.
   * 
   * Requirements: 2.1 - Create ECR repository for storing MCP server Docker images
   * Requirements: 2.2 - Configure image scanning on push for vulnerability detection
   * Requirements: 2.3 - Set lifecycle policies to retain only the last 10 images
   * 
   * @returns The configured ECR repository
   */
  private createEcrRepository(): ecr.Repository {
    const repository = new ecr.Repository(this, 'McpServerRepository', {
      repositoryName: `${this.stackName.toLowerCase()}-mcp-server`,
      // Requirements: 2.2 - Configure image scanning on push
      imageScanOnPush: true,
      // Enable removal policy for cleanup (can be changed to RETAIN for production)
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      // Empty the repository on stack deletion
      emptyOnDelete: true,
    });

    // Requirements: 2.3 - Set lifecycle policy to retain last 10 images
    repository.addLifecycleRule({
      description: 'Retain only the last 10 images',
      maxImageCount: 10,
      rulePriority: 1,
    });

    return repository;
  }

  /**
   * Creates a Docker image asset that builds and pushes the MCP server image to ECR.
   * 
   * CDK automatically handles:
   * 1. Building the Docker image from the Dockerfile
   * 2. Pushing the image to an ECR repository
   * 3. Managing image tags based on content hash
   * 
   * Requirements: 2.4 - WHEN deploying the stack THEN build and push the Docker image to ECR
   * 
   * @param props - Stack properties containing Docker build configuration
   * @returns The Docker image asset
   */
  private createDockerImageAsset(props?: McpFargateStackProps): ecr_assets.DockerImageAsset {
    const dockerBuildContext = props?.dockerBuildContext ?? DEFAULT_STACK_CONFIG.dockerBuildContext;

    return new ecr_assets.DockerImageAsset(this, 'McpServerImage', {
      directory: dockerBuildContext,
      // Platform targeting for Fargate (linux/amd64)
      platform: ecr_assets.Platform.LINUX_AMD64,
      // Exclude unnecessary files from the build context
      exclude: [
        '**/__pycache__',
        '**/*.pyc',
        '**/.pytest_cache',
        '**/.git',
        '**/node_modules',
        '**/.env',
        '**/.venv',
        '**/venv',
      ],
    });
  }

  /**
   * Creates the IAM task execution role for ECS.
   * 
   * This role is assumed by the ECS agent to:
   * - Pull container images from ECR
   * - Write logs to CloudWatch Logs
   * - Read secrets from Secrets Manager
   * 
   * Requirements: 5.1 - Create IAM task execution role for ECS to pull images and write logs
   * 
   * @returns The task execution role
   */
  private createTaskExecutionRole(): iam.Role {
    const executionRole = new iam.Role(this, 'TaskExecutionRole', {
      roleName: `${this.stackName}-task-execution-role`,
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'IAM role for ECS task execution - pulling images, writing logs, reading secrets',
    });

    // ECR pull permissions - allows ECS to pull container images
    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'ECRPullPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'ecr:GetAuthorizationToken',
      ],
      resources: ['*'], // GetAuthorizationToken requires * resource
    }));

    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'ECRImagePullPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'ecr:BatchCheckLayerAvailability',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
      ],
      resources: [
        this.ecrRepository.repositoryArn,
        // Also allow pulling from CDK-managed ECR repository for DockerImageAsset
        `arn:aws:ecr:${this.region}:${this.account}:repository/cdk-*`,
      ],
    }));

    // CloudWatch Logs write permissions - allows ECS to send container logs
    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'CloudWatchLogsPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: [
        `arn:aws:logs:${this.region}:${this.account}:log-group:/ecs/${this.stackName}*:*`,
      ],
    }));

    // Secrets Manager read permissions - allows ECS to inject secrets into containers
    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'SecretsManagerReadPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue',
      ],
      resources: [
        `arn:aws:secretsmanager:${this.region}:${this.account}:secret:${this.stackName}*`,
      ],
    }));

    return executionRole;
  }

  /**
   * Creates the IAM task role for the application.
   * 
   * This role is assumed by the application running in the container to:
   * - Invoke Amazon Bedrock models for AI inference
   * - Read secrets from Secrets Manager at runtime
   * 
   * Requirements: 5.2 - Create IAM task role for MCP server to invoke Bedrock models
   * Requirements: 5.3 - IAM_Task_Role SHALL have permissions to invoke Amazon Bedrock models
   * Requirements: 5.4 - IAM_Task_Role SHALL have permissions to read secrets from Secrets Manager
   * Requirements: 8.1 - IAM_Task_Role SHALL have permissions to invoke bedrock:InvokeModel
   * 
   * @param props - Stack properties containing Bedrock configuration
   * @returns The task role
   */
  private createTaskRole(props?: McpFargateStackProps): iam.Role {
    const bedrockRegion = props?.bedrockRegion ?? this.region;

    const taskRole = new iam.Role(this, 'TaskRole', {
      roleName: `${this.stackName}-task-role`,
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'IAM role for MCP server application - Bedrock invocation and secrets access',
    });

    // Bedrock InvokeModel permissions - allows the application to call Bedrock models
    // Requirements: 5.3, 8.1 - Permissions to invoke Amazon Bedrock models
    taskRole.addToPolicy(new iam.PolicyStatement({
      sid: 'BedrockInvokeModelPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: [
        // Allow invoking any foundation model in the configured region
        `arn:aws:bedrock:${bedrockRegion}::foundation-model/*`,
      ],
    }));

    // Secrets Manager read permissions - allows the application to read secrets at runtime
    // Requirements: 5.4 - Permissions to read secrets from Secrets Manager
    taskRole.addToPolicy(new iam.PolicyStatement({
      sid: 'SecretsManagerReadPermissions',
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue',
      ],
      resources: [
        `arn:aws:secretsmanager:${this.region}:${this.account}:secret:${this.stackName}*`,
      ],
    }));

    return taskRole;
  }

  /**
   * Creates optional Secrets Manager secrets for API keys.
   * 
   * These secrets are created as placeholders - the actual API key values
   * should be set manually in the AWS Console or via CLI after deployment.
   * 
   * Requirements: 6.1 - Create Secrets Manager secrets for optional API keys (OpenAI, Anthropic)
   * 
   * @param props - Stack properties containing secrets configuration
   * @returns Object containing the created secrets (undefined if not requested)
   */
  private createOptionalSecrets(props?: McpFargateStackProps): {
    openAiSecret?: secretsmanager.Secret;
    anthropicSecret?: secretsmanager.Secret;
  } {
    const createOpenAiSecret = props?.createOpenAiSecret ?? DEFAULT_STACK_CONFIG.createOpenAiSecret;
    const createAnthropicSecret = props?.createAnthropicSecret ?? DEFAULT_STACK_CONFIG.createAnthropicSecret;

    let openAiSecret: secretsmanager.Secret | undefined;
    let anthropicSecret: secretsmanager.Secret | undefined;

    // Create OpenAI API key secret when createOpenAiSecret is true
    if (createOpenAiSecret) {
      openAiSecret = new secretsmanager.Secret(this, 'OpenAiApiKeySecret', {
        secretName: `${this.stackName}/openai-api-key`,
        description: 'OpenAI API key for the MCP server. Set the value manually after deployment.',
        // Generate a placeholder value - should be replaced with actual API key
        generateSecretString: {
          secretStringTemplate: JSON.stringify({ apiKey: 'PLACEHOLDER_REPLACE_ME' }),
          generateStringKey: 'placeholder',
          excludePunctuation: true,
        },
      });

      // Add resource-based policy to allow the task role to read this secret
      openAiSecret.grantRead(this.taskRole);
      openAiSecret.grantRead(this.taskExecutionRole);
    }

    // Create Anthropic API key secret when createAnthropicSecret is true
    if (createAnthropicSecret) {
      anthropicSecret = new secretsmanager.Secret(this, 'AnthropicApiKeySecret', {
        secretName: `${this.stackName}/anthropic-api-key`,
        description: 'Anthropic API key for the MCP server. Set the value manually after deployment.',
        // Generate a placeholder value - should be replaced with actual API key
        generateSecretString: {
          secretStringTemplate: JSON.stringify({ apiKey: 'PLACEHOLDER_REPLACE_ME' }),
          generateStringKey: 'placeholder',
          excludePunctuation: true,
        },
      });

      // Add resource-based policy to allow the task role to read this secret
      anthropicSecret.grantRead(this.taskRole);
      anthropicSecret.grantRead(this.taskExecutionRole);
    }

    return {
      openAiSecret,
      anthropicSecret,
    };
  }

  /**
   * Creates a CloudWatch log group for container logs.
   * 
   * The log group name is based on the stack name to ensure uniqueness
   * and easy identification. Retention is set to 30 days as per requirements.
   * 
   * Requirements: 7.1 - Create CloudWatch log group for container logs
   * Requirements: 7.3 - Set log retention to 30 days
   * 
   * @returns The CloudWatch log group
   */
  private createLogGroup(): logs.LogGroup {
    return new logs.LogGroup(this, 'McpServerLogGroup', {
      // Configure log group name based on stack name
      logGroupName: `/ecs/${this.stackName}/mcp-server`,
      // Set retention to 30 days as per requirements
      retention: logs.RetentionDays.ONE_MONTH,
      // Enable removal policy for cleanup (can be changed to RETAIN for production)
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
  }

  /**
   * Creates an ECS cluster with Fargate capacity provider.
   * 
   * The cluster is configured to use Fargate for serverless container execution.
   * Container insights are enabled for enhanced monitoring.
   * 
   * Requirements: 3.1 - Create ECS cluster with Fargate capacity providers
   * 
   * @returns The ECS cluster
   */
  private createEcsCluster(): ecs.Cluster {
    return new ecs.Cluster(this, 'McpEcsCluster', {
      clusterName: `${this.stackName}-cluster`,
      vpc: this.vpc,
      // Enable container insights for enhanced monitoring
      containerInsights: true,
      // Fargate capacity provider is enabled by default
    });
  }

  /**
   * Creates the ECS task definition with container configuration.
   * 
   * Configures:
   * - CPU and memory from props
   * - Container image from DockerImageAsset
   * - CloudWatch logging with awslogs driver
   * - Environment variables for AWS region
   * - Secrets injection from Secrets Manager
   * 
   * Requirements: 3.2 - Define task definition with appropriate CPU and memory allocation
   * Requirements: 3.5 - Configure container logging to CloudWatch Logs
   * Requirements: 6.2 - Inject secrets as environment variables from Secrets Manager
   * Requirements: 7.2 - Configure awslogs driver to send logs to CloudWatch
   * Requirements: 8.2 - Configure AWS region for Bedrock access
   * 
   * Note: Bedrock model ID is configured in config.json, not via environment variables
   * 
   * @param props - Stack properties containing ECS and container configuration
   * @returns The Fargate task definition
   */
  private createTaskDefinition(props?: McpFargateStackProps): ecs.FargateTaskDefinition {
    const cpu = props?.cpu ?? DEFAULT_STACK_CONFIG.cpu;
    const memoryMiB = props?.memoryMiB ?? DEFAULT_STACK_CONFIG.memoryMiB;
    const containerPort = props?.containerPort ?? DEFAULT_STACK_CONFIG.containerPort;
    const bedrockRegion = props?.bedrockRegion ?? this.region;
    const healthCheckPath = props?.healthCheckPath ?? DEFAULT_STACK_CONFIG.healthCheckPath;

    // Create Fargate task definition with configured CPU and memory
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'McpTaskDefinition', {
      family: `${this.stackName}-task`,
      cpu: cpu,
      memoryLimitMiB: memoryMiB,
      executionRole: this.taskExecutionRole,
      taskRole: this.taskRole,
    });

    // Build secrets map for container
    const secrets: { [key: string]: ecs.Secret } = {};
    
    if (this.openAiApiKeySecret) {
      secrets['OPENAI_API_KEY'] = ecs.Secret.fromSecretsManager(
        this.openAiApiKeySecret,
        'apiKey'
      );
    }
    
    if (this.anthropicApiKeySecret) {
      secrets['ANTHROPIC_API_KEY'] = ecs.Secret.fromSecretsManager(
        this.anthropicApiKeySecret,
        'apiKey'
      );
    }

    // Add container to task definition
    const container = taskDefinition.addContainer('McpServerContainer', {
      containerName: 'mcp-server',
      // Use dockerImageAsset.imageUri for container image
      image: ecs.ContainerImage.fromDockerImageAsset(this.dockerImageAsset),
      // Configure awslogs driver for CloudWatch
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'mcp-server',
        logGroup: this.logGroup,
      }),
      // Set environment variables
      // Note: BEDROCK_MODEL_ID removed - model_id is configured in config.json extraction section
      environment: {
        AWS_REGION: bedrockRegion,
        LOG_LEVEL: 'INFO',
        MCP_TRANSPORT: 'streamable-http',
        FASTMCP_STATELESS_HTTP: 'true',
        // Using stateful mode with single task - stateless mode has protocol compatibility issues with Kiro
      },
      // Inject secrets from Secrets Manager
      secrets: Object.keys(secrets).length > 0 ? secrets : undefined,
      // Container port mapping
      portMappings: [
        {
          containerPort: containerPort,
          protocol: ecs.Protocol.TCP,
        },
      ],
      // Health check configuration
      healthCheck: {
        command: ['CMD-SHELL', `curl -f http://localhost:${containerPort}${healthCheckPath} || exit 1`],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    return taskDefinition;
  }

  /**
   * Creates the ECS Fargate service.
   * 
   * Configures:
   * - Desired task count from props (default: 2 for high availability)
   * - Placement in private subnets
   * - Health check grace period
   * 
   * Requirements: 3.3 - Run at least 2 tasks for high availability
   * Requirements: 3.4 - Automatically replace unhealthy tasks
   * 
   * @param props - Stack properties containing service configuration
   * @returns The Fargate service
   */
  private createFargateService(props?: McpFargateStackProps): ecs.FargateService {
    const desiredCount = props?.desiredCount ?? DEFAULT_STACK_CONFIG.desiredCount;

    // Create security group for Fargate tasks
    const serviceSecurityGroup = new ec2.SecurityGroup(this, 'FargateServiceSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for MCP Fargate service',
      allowAllOutbound: true,
    });

    // Create Fargate service
    const service = new ecs.FargateService(this, 'McpFargateService', {
      serviceName: `${this.stackName}-service`,
      cluster: this.ecsCluster,
      taskDefinition: this.taskDefinition,
      // Set desired count from props (default: 2 for high availability)
      desiredCount: desiredCount,
      // Place in private subnets
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [serviceSecurityGroup],
      // Enable circuit breaker for automatic rollback on deployment failures
      circuitBreaker: {
        rollback: true,
      },
      // Health check grace period to allow container startup
      healthCheckGracePeriod: cdk.Duration.seconds(60),
      // Enable ECS managed tags
      enableECSManagedTags: true,
      // Propagate tags from service to tasks
      propagateTags: ecs.PropagatedTagSource.SERVICE,
    });

    return service;
  }

  /**
   * Creates the Application Load Balancer in public subnets.
   * 
   * Configures:
   * - Internet-facing ALB in public subnets
   * - Security group allowing port 80 inbound
   * 
   * Requirements: 4.1 - Create internet-facing Application Load Balancer in public subnets
   * Requirements: 1.4 - Create security groups that restrict inbound traffic to only necessary ports
   * 
   * @param props - Stack properties (unused but kept for consistency)
   * @returns Object containing the ALB and its security group
   */
  private createApplicationLoadBalancer(props?: McpFargateStackProps): {
    alb: elbv2.ApplicationLoadBalancer;
    securityGroup: ec2.SecurityGroup;
  } {
    // Create security group for ALB allowing port 80 inbound
    const albSecurityGroup = new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for MCP Application Load Balancer',
      allowAllOutbound: true,
    });

    // Allow inbound HTTP traffic on port 80 from anywhere
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP traffic from anywhere'
    );

    // Create internet-facing ALB in public subnets
    const alb = new elbv2.ApplicationLoadBalancer(this, 'McpAlb', {
      loadBalancerName: `${this.stackName}-alb`,
      vpc: this.vpc,
      internetFacing: true,
      securityGroup: albSecurityGroup,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
    });

    return {
      alb,
      securityGroup: albSecurityGroup,
    };
  }

  /**
   * Creates the target group and HTTP listener for the ALB.
   * 
   * Configures:
   * - Target group with health check
   * - HTTP listener on port 80
   * - Registers Fargate service as target
   * - Allows ALB to communicate with Fargate tasks
   * 
   * Requirements: 4.2 - ALB SHALL perform health checks on target containers
   * Requirements: 4.3 - ALB SHALL route HTTP traffic on port 80 to the Fargate service
   * Requirements: 1.5 - Route traffic only to containers in private subnets
   * 
   * @param props - Stack properties containing health check configuration
   * @returns Object containing the target group and listener
   */
  private createTargetGroupAndListener(props?: McpFargateStackProps): {
    targetGroup: elbv2.ApplicationTargetGroup;
    listener: elbv2.ApplicationListener;
  } {
    const containerPort = props?.containerPort ?? DEFAULT_STACK_CONFIG.containerPort;
    const healthCheckPath = props?.healthCheckPath ?? DEFAULT_STACK_CONFIG.healthCheckPath;

    // Create HTTP listener on port 80
    const listener = this.alb.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      open: true,
    });

    // Create target group and register Fargate service
    const targetGroup = listener.addTargets('FargateTargetGroup', {
      targetGroupName: `${this.stackName}-tg`,
      port: containerPort,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [this.fargateService],
      // Configure health check on target group
      healthCheck: {
        path: healthCheckPath,
        protocol: elbv2.Protocol.HTTP,
        healthyHttpCodes: '200',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
      },
      // Deregistration delay for graceful shutdown
      deregistrationDelay: cdk.Duration.seconds(30),
      // Enable sticky sessions for MCP session management
      stickinessCookieDuration: cdk.Duration.hours(1),
    });

    // Allow ALB to communicate with Fargate tasks on the container port
    this.fargateService.connections.allowFrom(
      this.albSecurityGroup,
      ec2.Port.tcp(containerPort),
      'Allow traffic from ALB to Fargate tasks'
    );

    return {
      targetGroup,
      listener,
    };
  }
}
