---
inclusion: manual
---

# Fixed Schema Response MCP Server

This steering file provides information about using the Fixed Schema Response MCP Server with Kiro.

## Available Schemas

The Fixed Schema MCP Server supports the following schemas:

### 1. Product Info (`product_info`)
- For generating structured information about products
- Includes name, description, price, category, and features

### 2. Article Summary (`article_summary`)
- For generating structured summaries of articles or topics
- Includes title, summary, key points, and sentiment

### 3. Person Profile (`person_profile`)
- For generating structured biographical information about people
- Includes name, bio, expertise, achievements, education, career, and impact

### 4. API Endpoint Documentation (`api_endpoint`)
- For generating structured API endpoint documentation
- Includes endpoint path, HTTP method, description, parameters, request body, responses, authentication, and examples

### 5. Troubleshooting Guide (`troubleshooting_guide`)
- For generating structured technical troubleshooting guides
- Includes issue description, summary, symptoms, affected systems, root causes, solutions, prevention measures, and references

## Usage Examples

To use the Fixed Schema MCP Server in Kiro, use the following format:

```
@fixed-schema <query> --schema <schema_name>
```

Examples:

```
@fixed-schema Tell me about the latest iPhone --schema product_info
@fixed-schema Summarize the latest news about AI advancements --schema article_summary
@fixed-schema Ada Lovelace --schema person_profile
@fixed-schema Create a user API endpoint --schema api_endpoint
@fixed-schema How to fix Docker container not starting --schema troubleshooting_guide
```

## Tips for Best Results

1. Be specific in your queries to get more accurate structured responses
2. Choose the appropriate schema for your use case
3. For person profiles, include the full name and any relevant context
4. For API endpoints, specify the purpose and key functionality
5. For troubleshooting guides, clearly describe the issue you're trying to solve