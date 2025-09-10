# Security Best Practices for FastMCP Server

This document outlines security best practices, potential vulnerabilities, and recommended configurations for the FastMCP server implementation.

## Security Analysis Results

### ✅ Security Improvements Implemented

1. **Input Validation Enhanced**
   - Schema name validation with regex pattern matching
   - Path traversal protection in file operations
   - JSON schema validation with dangerous property filtering
   - System prompt length and content validation

2. **Logging Security**
   - Removed sensitive data from logs (prompts, responses)
   - Added log message sanitization utilities
   - Configurable logging levels for security

3. **File System Security**
   - Path validation to prevent directory traversal
   - File extension restrictions
   - Existence checks before file operations

4. **Configuration Security**
   - Externalized security constants
   - Secure default configurations
   - Model ID configuration instead of hardcoding

## Security Recommendations

### 1. Credential Management

**Current Risk**: AWS credentials in configuration files
**Recommendation**: Use AWS IAM roles or environment variables

```bash
# Preferred: Use IAM roles (for EC2/ECS/Lambda)
# Or use environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2
```

**Configuration**:
```json
{
  "model": {
    "provider": "aws_bedrock",
    "credentials": {
      "aws_region": "us-west-2"
      // Remove explicit credentials - use IAM roles or env vars
    }
  }
}
```

### 2. Network Security

**Recommendations**:
- Run server in private network/VPC
- Use TLS/SSL for all communications
- Implement rate limiting
- Add request size limits

### 3. Input Validation

**Implemented Validations**:
- Schema name: alphanumeric, underscore, hyphen only
- Maximum lengths for all inputs
- JSON schema structure validation
- Path traversal prevention

**Additional Recommendations**:
```python
# Add to your configuration
{
  "security": {
    "max_request_size": 1048576,  # 1MB
    "rate_limit_per_minute": 60,
    "enable_request_logging": false
  }
}
```

### 4. Error Handling

**Best Practices**:
- Don't expose internal paths in error messages
- Log security events for monitoring
- Use generic error messages for users
- Implement proper exception handling

### 5. Monitoring and Logging

**Security Logging**:
```python
# Log security events
logger.warning(f"Invalid schema name attempted: {sanitized_name}")
logger.error(f"Path traversal attempt detected from client")
logger.info(f"Schema creation rate limit exceeded for client")
```

**Recommended Log Monitoring**:
- Failed authentication attempts
- Invalid input patterns
- File system access attempts
- Rate limit violations

## Deployment Security

### 1. Container Security

```dockerfile
# Use non-root user
FROM python:3.11-slim
RUN useradd -m -u 1000 mcpuser
USER mcpuser

# Set secure file permissions
COPY --chown=mcpuser:mcpuser . /app
RUN chmod 755 /app
```

### 2. Environment Variables

```bash
# Required environment variables
AWS_REGION=us-west-2
FASTMCP_LOG_LEVEL=INFO
MCP_SERVER_TIMEOUT=30

# Optional security settings
MCP_ENABLE_REQUEST_LOGGING=false
MCP_MAX_REQUEST_SIZE=1048576
MCP_RATE_LIMIT=60
```

### 3. AWS IAM Policy

Minimal IAM policy for Bedrock access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-*"
      ]
    }
  ]
}
```

## Security Testing

### 1. Input Validation Tests

```python
# Test malicious schema names
test_cases = [
    "../../../etc/passwd",
    "schema;rm -rf /",
    "schema<script>alert('xss')</script>",
    "a" * 1000,  # Length test
    "schema\x00null"  # Null byte injection
]
```

### 2. File System Tests

```python
# Test path traversal attempts
dangerous_paths = [
    "../../config.json",
    "/etc/passwd",
    "C:\\Windows\\System32\\config\\SAM",
    "schema/../../../sensitive_file"
]
```

### 3. Rate Limiting Tests

```bash
# Test rate limiting
for i in {1..100}; do
  curl -X POST http://localhost:8000/schema \
    -d '{"name":"test'$i'","schema":"{}"}' &
done
```

## Compliance Considerations

### 1. Data Privacy

- **PII Handling**: Ensure no personally identifiable information is logged
- **Data Retention**: Implement log rotation and retention policies
- **Encryption**: Use encryption at rest and in transit

### 2. Access Control

- **Authentication**: Implement proper authentication mechanisms
- **Authorization**: Role-based access control for different operations
- **Audit Trail**: Maintain audit logs for all operations

### 3. Regulatory Compliance

- **GDPR**: Implement data subject rights (deletion, portability)
- **SOC 2**: Implement security controls and monitoring
- **HIPAA**: Additional encryption and access controls if handling health data

## Security Checklist

- [ ] Remove hardcoded credentials
- [ ] Implement rate limiting
- [ ] Add request size limits
- [ ] Enable security logging
- [ ] Set up log monitoring
- [ ] Use HTTPS/TLS
- [ ] Implement authentication
- [ ] Regular security updates
- [ ] Penetration testing
- [ ] Security code review

## Incident Response

### 1. Security Event Detection

Monitor for:
- Unusual request patterns
- Failed authentication attempts
- File system access violations
- Rate limit violations

### 2. Response Procedures

1. **Immediate**: Block suspicious IP addresses
2. **Investigation**: Analyze logs and determine impact
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore from clean backups if needed
5. **Lessons Learned**: Update security measures

## Contact

For security issues or questions:
- Create a private security issue in the repository
- Follow responsible disclosure practices
- Include detailed reproduction steps

---

**Note**: This document should be reviewed and updated regularly as new security threats and best practices emerge.