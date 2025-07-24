---
inclusion: manual
---

# Fixed Schema Response MCP Server (FastMCP Edition)

This steering file provides information about using the Fixed Schema Response MCP Server with Kiro.

## Available Tools

The Fixed Schema MCP Server provides the following tools:

### 1. Product Info (`get_product_info`)
- For generating structured information about products
- Includes name, description, price, category, features, rating, and availability
- Example: `@fixed-schema get_product_info product_name: "iPhone 15 Pro"`

### 2. Article Summary (`get_article_summary`)
- For generating structured summaries of articles or topics
- Includes title, author, date, summary, key points, and conclusion
- Example: `@fixed-schema get_article_summary topic: "artificial intelligence"`

### 3. Person Profile (`get_person_profile`)
- For generating structured biographical information about people
- Includes name, age, occupation, skills, and contact information
- Example: `@fixed-schema get_person_profile person_name: "Elon Musk"`

### 4. API Endpoint Documentation (`get_api_endpoint`)
- For generating structured API endpoint documentation
- Includes path, method, description, parameters, and responses
- Example: `@fixed-schema get_api_endpoint endpoint_name: "user authentication"`

### 5. Troubleshooting Guide (`get_troubleshooting_guide`)
- For generating structured technical troubleshooting guides
- Includes issue, symptoms, causes, step-by-step solutions, and prevention tips
- Example: `@fixed-schema get_troubleshooting_guide issue: "computer won't start"`

## Usage Examples

```
@fixed-schema get_product_info product_name: "MacBook Pro M3"
@fixed-schema get_article_summary topic: "quantum computing"
@fixed-schema get_person_profile person_name: "Ada Lovelace"
@fixed-schema get_api_endpoint endpoint_name: "payment processing"
@fixed-schema get_troubleshooting_guide issue: "Docker container not starting"
```

## Tips for Best Results

1. Be specific in your queries to get more accurate structured responses
2. Choose the appropriate tool for your use case
3. For person profiles, include the full name
4. For API endpoints, specify the purpose clearly
5. For troubleshooting guides, clearly describe the issue you're trying to solve

## Note on AWS Integration

The server uses AWS Bedrock Claude 4 Sonnet for generating responses when AWS credentials are available. If AWS credentials are not configured, the server will automatically fall back to mock responses.