# AWS Deployment Guide for Fixed Schema MCP Server

This guide provides detailed instructions for deploying the Fixed Schema MCP Server to AWS and implementing JWT authentication.

## Deploying to AWS Cloud

To deploy the Fixed Schema MCP Server to AWS and expose it via an endpoint, you have several options. Here's a comprehensive design using AWS services that would provide scalability, reliability, and security:

### Architecture Overview

![AWS Architecture Diagram](https://i.imgur.com/example.png)

### Option 1: Container-based Deployment (Recommended)

#### AWS Services:
1. **Amazon ECS (Elastic Container Service) with Fargate**
   - Serverless container orchestration
   - No need to manage EC2 instances
   - Automatic scaling based on demand

2. **Amazon ECR (Elastic Container Registry)**
   - Store your Docker images securely
   - Integrates seamlessly with ECS

3. **Application Load Balancer (ALB)**
   - Route traffic to your containers
   - Support for WebSockets (important for MCP protocol)
   - SSL/TLS termination

4. **Amazon API Gateway (WebSocket API)**
   - Alternative to ALB if you need more advanced API management
   - Built-in WebSocket support
   - Request throttling and authorization

5. **AWS Secrets Manager**
   - Store API keys and credentials securely
   - Rotate secrets automatically

#### Implementation Steps:

1. **Containerize the MCP Server**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   # Install the package
   RUN pip install -e .
   
   # Expose the port
   EXPOSE 8000
   
   # Run the server
   CMD ["fixed-schema-mcp-server", "--config", "config.json"]
   ```

2. **Build and Push to ECR**
   ```bash
   aws ecr create-repository --repository-name fixed-schema-mcp-server
   docker build -t fixed-schema-mcp-server .
   aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
   docker tag fixed-schema-mcp-server:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/fixed-schema-mcp-server:latest
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/fixed-schema-mcp-server:latest
   ```

3. **Create ECS Cluster and Task Definition**
   - Use AWS Console or CloudFormation/CDK
   - Define CPU and memory requirements
   - Configure environment variables for configuration

4. **Set Up Load Balancer and Target Group**
   - Create ALB with WebSocket support
   - Configure health checks
   - Set up security groups

5. **Create ECS Service**
   - Connect to the load balancer
   - Configure desired number of tasks
   - Set up auto-scaling policies

### Option 2: Serverless Deployment

#### AWS Services:
1. **AWS Lambda**
   - Serverless compute
   - Pay only for what you use
   - Automatic scaling

2. **Amazon API Gateway (HTTP API or WebSocket API)**
   - Route requests to Lambda functions
   - WebSocket support for real-time communication

3. **AWS Lambda Container Images**
   - Package your application as a container
   - Up to 10GB container size

#### Implementation Considerations:
- Lambda has execution time limits (15 minutes max)
- Cold starts might affect performance
- WebSocket connections require special handling with API Gateway + Lambda

### Option 3: Traditional EC2 Deployment

#### AWS Services:
1. **Amazon EC2**
   - Full control over the environment
   - Choose instance types based on workload
   - Auto Scaling Groups for high availability

2. **Elastic Load Balancer**
   - Distribute traffic across instances
   - SSL/TLS termination

3. **Amazon Route 53**
   - DNS management
   - Health checks and failover

## Security Considerations

1. **Network Security**
   - Use VPC with private subnets for containers/instances
   - Security groups to restrict traffic
   - Network ACLs for additional protection

2. **Authentication & Authorization**
   - API Gateway authorization (API keys, IAM, Cognito)
   - JWT token validation
   - Custom authorizers

3. **Data Protection**
   - Encryption in transit (HTTPS/TLS)
   - Encryption at rest for sensitive data
   - AWS KMS for key management

## Monitoring and Observability

1. **Amazon CloudWatch**
   - Logs, metrics, and alarms
   - Custom dashboards

2. **AWS X-Ray**
   - Distributed tracing
   - Performance analysis

3. **Amazon CloudWatch Synthetics**
   - Canary testing
   - Endpoint monitoring

## Cost Optimization

1. **Fargate Spot (for non-critical workloads)**
   - Up to 70% cost savings
   - Suitable for batch processing

2. **Reserved Instances (for EC2)**
   - For predictable workloads
   - Significant cost savings over on-demand

3. **Auto Scaling**
   - Scale based on demand
   - Scheduled scaling for predictable patterns

## Infrastructure as Code

Use AWS CDK or CloudFormation to define your infrastructure:

```typescript
// Example AWS CDK code (TypeScript)
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';

export class McpServerStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC
    const vpc = new ec2.Vpc(this, 'McpServerVpc', {
      maxAzs: 2
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'McpServerCluster', {
      vpc: vpc
    });

    // Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'McpServerTask', {
      memoryLimitMiB: 2048,
      cpu: 1024,
    });

    // Container
    const container = taskDefinition.addContainer('McpServerContainer', {
      image: ecs.ContainerImage.fromEcrRepository(
        ecr.Repository.fromRepositoryName(this, 'McpServerRepo', 'fixed-schema-mcp-server'),
        'latest'
      ),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'mcp-server' }),
      environment: {
        'FIXED_SCHEMA_MCP_LOG_LEVEL': 'INFO'
      },
    });

    container.addPortMappings({
      containerPort: 8000
    });

    // Fargate Service
    const service = new ecs.FargateService(this, 'McpServerService', {
      cluster,
      taskDefinition,
      desiredCount: 2,
      assignPublicIp: false,
    });

    // Load Balancer
    const lb = new elbv2.ApplicationLoadBalancer(this, 'McpServerLB', {
      vpc,
      internetFacing: true
    });

    const listener = lb.addListener('McpServerListener', {
      port: 443,
      certificates: [/* Add your ACM certificate */]
    });

    listener.addTargets('McpServerTarget', {
      port: 8000,
      targets: [service],
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30)
      }
    });

    // Output the load balancer DNS
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: lb.loadBalancerDnsName
    });
  }
}
```

## Recommended Approach

For the Fixed Schema MCP Server, I recommend the **ECS with Fargate** approach because:

1. It provides a good balance of scalability and manageability
2. WebSocket support through ALB or API Gateway
3. No server management overhead
4. Cost-effective for variable workloads
5. Easy integration with other AWS services

This architecture will give you a robust, scalable, and secure deployment of your MCP server that can handle production workloads while minimizing operational overhead.

# JWT Authentication/Authorization for Fixed Schema MCP Server on AWS

Implementing JWT (JSON Web Token) authentication and authorization for your Fixed Schema MCP Server provides a secure, stateless way to authenticate clients and control access to your API. Here's a comprehensive workflow and implementation strategy:

## JWT Authentication Workflow

![JWT Authentication Flow](https://i.imgur.com/example.png)

### 1. Authentication Flow

1. **Client Registration**
   - Users/clients register through a secure registration endpoint
   - Credentials stored securely (passwords hashed with bcrypt/Argon2)
   - User roles and permissions assigned

2. **Token Acquisition**
   - Client sends credentials to authentication endpoint
   - Server validates credentials
   - If valid, server generates and signs JWT tokens:
     - Access token (short-lived, e.g., 15-60 minutes)
     - Refresh token (longer-lived, e.g., 7-30 days)

3. **API Access**
   - Client includes access token in Authorization header
   - Server validates token signature, expiration, and claims
   - If valid, server processes the request
   - If invalid, server returns 401 Unauthorized

4. **Token Renewal**
   - When access token expires, client uses refresh token
   - Server validates refresh token and issues new access token
   - If refresh token is invalid or expired, user must re-authenticate

### 2. JWT Structure

```
Header.Payload.Signature
```

**Header Example:**
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**Payload Example:**
```json
{
  "sub": "1234567890",
  "name": "Client Name",
  "roles": ["user", "admin"],
  "permissions": ["read:schemas", "write:schemas"],
  "iat": 1516239022,
  "exp": 1516242622,
  "iss": "https://api.yourservice.com",
  "aud": "https://mcp.yourservice.com"
}
```

**Signature:**
Created using the header, payload, and a secret key or private key (for asymmetric algorithms).

## Implementation on AWS

### Option 1: Amazon Cognito (Recommended for Most Cases)

#### Architecture:
1. **Amazon Cognito User Pools**
   - Managed user directory
   - Built-in sign-up/sign-in flows
   - MFA support
   - Integration with social identity providers

2. **Amazon Cognito Identity Pools**
   - Map Cognito users to AWS IAM roles
   - Temporary AWS credentials for accessing AWS services

3. **API Gateway with Cognito Authorizer**
   - Validates JWT tokens issued by Cognito
   - Maps Cognito groups to API permissions

#### Implementation Steps:

1. **Create Cognito User Pool**
   ```bash
   aws cognito-idp create-user-pool \
     --pool-name MCPServerUserPool \
     --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":true}}' \
     --auto-verified-attributes email
   ```

2. **Create App Client**
   ```bash
   aws cognito-idp create-user-pool-client \
     --user-pool-id YOUR_USER_POOL_ID \
     --client-name MCPServerClient \
     --no-generate-secret \
     --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH
   ```

3. **Configure API Gateway with Cognito Authorizer**
   ```bash
   aws apigateway create-authorizer \
     --rest-api-id YOUR_API_ID \
     --name CognitoAuthorizer \
     --type COGNITO_USER_POOLS \
     --provider-arns arn:aws:cognito-idp:REGION:ACCOUNT_ID:userpool/USER_POOL_ID \
     --identity-source 'method.request.header.Authorization'
   ```

4. **Add Authorizer to API Methods**
   ```bash
   aws apigateway update-method \
     --rest-api-id YOUR_API_ID \
     --resource-id YOUR_RESOURCE_ID \
     --http-method POST \
     --patch-operations op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
     op=replace,path=/authorizerId,value=YOUR_AUTHORIZER_ID
   ```

### Option 2: Custom JWT Implementation

#### Architecture:
1. **Authentication Service (Lambda)**
   - Handles user registration and authentication
   - Issues and signs JWT tokens
   - Manages refresh tokens

2. **Token Validation Lambda**
   - Custom authorizer for API Gateway
   - Validates JWT signatures and claims
   - Maps JWT claims to IAM policies

3. **AWS Secrets Manager**
   - Stores JWT signing keys securely
   - Enables key rotation

#### Implementation Steps:

1. **Create JWT Authentication Lambda**
   ```javascript
   // Example Node.js Lambda function for JWT generation
   const jwt = require('jsonwebtoken');
   const AWS = require('aws-sdk');
   const secretsManager = new AWS.SecretsManager();

   exports.handler = async (event) => {
     // Get JWT signing key from Secrets Manager
     const secretData = await secretsManager.getSecretValue({
       SecretId: 'jwt/signing-key'
     }).promise();
     const signingKey = JSON.parse(secretData.SecretString).key;
     
     // Validate user credentials (from database or user service)
     // ...
     
     // Generate JWT token
     const token = jwt.sign({
       sub: userId,
       name: username,
       roles: userRoles,
       permissions: userPermissions
     }, signingKey, { 
       expiresIn: '1h',
       issuer: 'https://api.yourservice.com',
       audience: 'https://mcp.yourservice.com'
     });
     
     return {
       statusCode: 200,
       body: JSON.stringify({ token })
     };
   };
   ```

2. **Create Custom Authorizer Lambda**
   ```javascript
   // Example Node.js Lambda function for JWT validation
   const jwt = require('jsonwebtoken');
   const AWS = require('aws-sdk');
   const secretsManager = new AWS.SecretsManager();

   exports.handler = async (event) => {
     // Extract token from Authorization header
     const token = event.authorizationToken.replace('Bearer ', '');
     
     try {
       // Get JWT verification key from Secrets Manager
       const secretData = await secretsManager.getSecretValue({
         SecretId: 'jwt/signing-key'
       }).promise();
       const signingKey = JSON.parse(secretData.SecretString).key;
       
       // Verify token
       const decoded = jwt.verify(token, signingKey, {
         issuer: 'https://api.yourservice.com',
         audience: 'https://mcp.yourservice.com'
       });
       
       // Generate IAM policy based on JWT claims
       return generatePolicy(decoded.sub, 'Allow', event.methodArn, decoded);
     } catch (err) {
       console.error('Token validation failed:', err);
       throw new Error('Unauthorized');
     }
   };
   
   function generatePolicy(principalId, effect, resource, context) {
     const authResponse = {
       principalId,
       policyDocument: {
         Version: '2012-10-17',
         Statement: [{
           Action: 'execute-api:Invoke',
           Effect: effect,
           Resource: resource
         }]
       },
       context
     };
     return authResponse;
   }
   ```

3. **Configure API Gateway with Custom Authorizer**
   ```bash
   aws apigateway create-authorizer \
     --rest-api-id YOUR_API_ID \
     --name JwtAuthorizer \
     --type REQUEST \
     --authorizer-uri arn:aws:apigateway:REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:REGION:ACCOUNT_ID:function:JwtAuthorizerFunction/invocations \
     --identity-source 'method.request.header.Authorization'
   ```

### Option 3: AWS Lambda Authorizer with Auth0

#### Architecture:
1. **Auth0 Tenant**
   - Managed authentication service
   - Social login providers
   - MFA support
   - Role-based access control

2. **Lambda Authorizer**
   - Validates JWT tokens issued by Auth0
   - Maps Auth0 roles to API permissions

#### Implementation Steps:

1. **Set Up Auth0 Application**
   - Create a new application in Auth0 dashboard
   - Configure callback URLs
   - Set up API audience

2. **Create Lambda Authorizer**
   ```javascript
   // Example Node.js Lambda function for Auth0 JWT validation
   const jwt = require('jsonwebtoken');
   const jwksClient = require('jwks-rsa');

   const client = jwksClient({
     jwksUri: 'https://YOUR_AUTH0_DOMAIN/.well-known/jwks.json'
   });

   function getSigningKey(kid) {
     return new Promise((resolve, reject) => {
       client.getSigningKey(kid, (err, key) => {
         if (err) return reject(err);
         const signingKey = key.publicKey || key.rsaPublicKey;
         resolve(signingKey);
       });
     });
   }

   exports.handler = async (event) => {
     const token = event.authorizationToken.replace('Bearer ', '');
     
     try {
       // Get token header
       const decodedToken = jwt.decode(token, { complete: true });
       if (!decodedToken) throw new Error('Invalid token');
       
       // Get signing key
       const signingKey = await getSigningKey(decodedToken.header.kid);
       
       // Verify token
       const verified = jwt.verify(token, signingKey, {
         audience: 'https://mcp.yourservice.com',
         issuer: 'https://YOUR_AUTH0_DOMAIN/'
       });
       
       return generatePolicy(verified.sub, 'Allow', event.methodArn, {
         scope: verified.scope,
         permissions: verified.permissions
       });
     } catch (err) {
       console.error('Token validation failed:', err);
       throw new Error('Unauthorized');
     }
   };
   ```

## Advanced JWT Features

### 1. Token Revocation

Implement a token blacklist using:
- **Amazon DynamoDB** for storing revoked tokens
- **Amazon ElastiCache (Redis)** for high-performance token blacklist

```javascript
// Check if token is revoked before validating
async function isTokenRevoked(jti) {
  const params = {
    TableName: 'RevokedTokens',
    Key: { jti }
  };
  
  const result = await dynamoDB.get(params).promise();
  return !!result.Item;
}
```

### 2. Fine-grained Authorization

Use JWT claims for detailed permission checks:

```javascript
// Example permission check in your MCP server
function checkPermission(decodedToken, requiredPermission) {
  if (!decodedToken.permissions) return false;
  return decodedToken.permissions.includes(requiredPermission);
}

// Usage
if (!checkPermission(decodedToken, 'read:schemas')) {
  return {
    statusCode: 403,
    body: JSON.stringify({ error: 'Insufficient permissions' })
  };
}
```

### 3. Token Refresh Strategy

Implement secure token refresh:

```javascript
// Example refresh token endpoint
async function refreshToken(refreshToken) {
  // Verify refresh token
  const decoded = jwt.verify(refreshToken, refreshTokenSecret);
  
  // Check if refresh token is in the database and not revoked
  const user = await getUserById(decoded.sub);
  if (!user || user.refreshToken !== refreshToken) {
    throw new Error('Invalid refresh token');
  }
  
  // Generate new access token
  const accessToken = jwt.sign({
    sub: user.id,
    roles: user.roles,
    permissions: user.permissions
  }, accessTokenSecret, { expiresIn: '1h' });
  
  return { accessToken };
}
```

## Security Best Practices

1. **Use Strong Algorithms**
   - RS256 (asymmetric) preferred over HS256 (symmetric)
   - Enables key rotation without client updates

2. **Include Essential Claims**
   - `iss` (issuer): Who issued the token
   - `sub` (subject): Who the token refers to
   - `exp` (expiration time): When the token expires
   - `iat` (issued at): When the token was issued
   - `aud` (audience): Who the token is intended for

3. **Keep Tokens Secure**
   - Store access tokens in memory (not localStorage)
   - Store refresh tokens in HttpOnly cookies
   - Implement CSRF protection for cookie-based tokens

4. **Implement Token Rotation**
   - Rotate signing keys regularly
   - Use AWS Secrets Manager for key management
   - Implement grace periods for key rotation

5. **Validate All Claims**
   - Verify signature
   - Check expiration time
   - Validate issuer and audience
   - Verify token hasn't been revoked

## Implementation in Fixed Schema MCP Server

To integrate JWT authentication with your Fixed Schema MCP Server:

1. **Add Authentication Middleware**
   ```python
   # Example middleware for Flask-based server
   from functools import wraps
   from flask import request, jsonify
   import jwt

   def jwt_required(f):
       @wraps(f)
       def decorated(*args, **kwargs):
           token = None
           
           if 'Authorization' in request.headers:
               auth_header = request.headers['Authorization']
               try:
                   token = auth_header.split(" ")[1]
               except IndexError:
                   return jsonify({'message': 'Token is missing or invalid'}), 401
           
           if not token:
               return jsonify({'message': 'Token is missing'}), 401
               
           try:
               # Verify token
               payload = jwt.decode(
                   token, 
                   current_app.config['JWT_SECRET_KEY'],
                   algorithms=['RS256'],
                   options={
                       'verify_signature': True,
                       'verify_exp': True,
                       'verify_nbf': True,
                       'verify_iat': True,
                       'verify_aud': True
                   },
                   audience='https://mcp.yourservice.com',
                   issuer='https://api.yourservice.com'
               )
               
               # Add user info to request context
               request.user = payload
               
           except jwt.ExpiredSignatureError:
               return jsonify({'message': 'Token has expired'}), 401
           except jwt.InvalidTokenError:
               return jsonify({'message': 'Invalid token'}), 401
               
           return f(*args, **kwargs)
       return decorated
   ```

2. **Apply Middleware to Routes**
   ```python
   @app.route('/query', methods=['POST'])
   @jwt_required
   def process_query():
       # Check specific permissions
       if 'read:schemas' not in request.user.get('permissions', []):
           return jsonify({'message': 'Insufficient permissions'}), 403
           
       # Process the query
       # ...
   ```

3. **Add Permission-Based Access Control**
   ```python
   def has_permission(permission):
       def decorator(f):
           @wraps(f)
           def decorated(*args, **kwargs):
               if permission not in request.user.get('permissions', []):
                   return jsonify({'message': f'Permission {permission} required'}), 403
               return f(*args, **kwargs)
           return decorated
       return decorator
       
   # Usage
   @app.route('/schemas', methods=['POST'])
   @jwt_required
   @has_permission('write:schemas')
   def create_schema():
       # Create schema
       # ...
   ```

## Conclusion

Implementing JWT authentication for your Fixed Schema MCP Server on AWS provides a secure, scalable, and flexible authentication mechanism. The recommended approach is to use Amazon Cognito for most cases due to its integration with AWS services and managed infrastructure. For more complex requirements, a custom JWT implementation or integration with Auth0 provides additional flexibility.

By following the security best practices outlined above, you can ensure that your MCP server is protected against common authentication vulnerabilities while providing a seamless experience for your clients.