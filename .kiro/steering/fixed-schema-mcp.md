---
inclusion: manual
---

# Generic Schema MCP Server (FastMCP Edition)

This steering file provides information about using the Generic Schema MCP Server with Kiro. This server dynamically loads JSON schemas and creates corresponding tools automatically.

## Available Tools

The Generic Schema MCP Server provides the following dynamically generated tools:

### Schema-Based Tools (Dynamically Generated) - 10 Total

### 1. API Endpoint Documentation (`get_api_endpoint`)
- For generating structured API endpoint documentation
- Includes endpoint, method, description, parameters, request body, responses, authentication, and examples
- Example: `@fixed-schema get_api_endpoint query: "user authentication API"`

### 2. Article Summary (`get_article_summary`)
- For generating structured summaries of articles or topics
- Includes title, summary, key points, and sentiment analysis
- Example: `@fixed-schema get_article_summary query: "artificial intelligence trends"`

### 3. Book Review (`get_book_review`)
- For generating structured book reviews and literary analysis
- Includes title, author, rating, detailed review, genres, and recommendation
- Example: `@fixed-schema get_book_review query: "The Great Gatsby by F. Scott Fitzgerald"`

### 4. Movie Review (`get_movie_review`)
- For generating structured movie reviews and ratings
- Includes title, director, year, genre, rating, review, pros, cons, and recommendation
- Example: `@fixed-schema get_movie_review query: "The Matrix"`

### 5. Person Profile (`get_person_profile`)
- For generating structured biographical information about people
- Includes name, bio, expertise, achievements, education, career, and impact
- Example: `@fixed-schema get_person_profile query: "Elon Musk"`

### 6. Product Info (`get_product_info`)
- For generating structured information about products
- Includes name, description, price, category, and features
- Example: `@fixed-schema get_product_info query: "iPhone 15 Pro"`

### 7. Recipe (`get_recipe`)
- For generating structured cooking recipes
- Includes name, description, ingredients, instructions, prep time, cook time, servings, and difficulty
- Example: `@fixed-schema get_recipe query: "chocolate chip cookies"`

### 8. Sports Stats (`get_sports_stats`)
- For generating structured sports player statistics and information
- Includes player name, sport, season, team, position, stats, and achievements
- Example: `@fixed-schema get_sports_stats query: "LeBron James 2023 season"`

### 9. Troubleshooting Guide (`get_troubleshooting_guide`)
- For generating structured technical troubleshooting guides
- Includes issue, summary, symptoms, affected systems, root causes, solutions, and prevention
- Example: `@fixed-schema get_troubleshooting_guide query: "Docker container won't start"`

### 10. Weather Report (`get_weather_report`)
- For generating structured weather information and forecasts
- Includes location, temperature, conditions, humidity, wind speed, and 3-day forecast
- Example: `@fixed-schema get_weather_report query: "San Francisco current weather"`

### Utility Tools

### 11. List Available Schemas (`list_available_schemas`)
- Lists all available schemas and their descriptions
- Shows current total count and tool names
- Example: `@fixed-schema list_available_schemas`

### 12. Add Schema (`add_schema`)
- Creates new schema files for persistent tool addition
- **Requires MCP server restart** to activate new tools
- Creates persistent .json files in test_config/schemas/
- Example: `@fixed-schema add_schema schema_name: "news_article" schema_definition: "{...}" description: "News article analysis" system_prompt: "You are a journalist..."`

## Quick Test Examples

Test the server with these simple commands:
```
@fixed-schema list_available_schemas
@fixed-schema get_weather_report query: "Weather in San Francisco"
@fixed-schema get_product_info query: "iPhone 15 Pro"
@fixed-schema get_recipe query: "chocolate chip cookies"
```

## Usage Examples

**Schema-based tools** (all accept a `query` parameter):
```
@fixed-schema get_weather_report query: "New York City current weather"
@fixed-schema get_product_info query: "MacBook Pro M3"
@fixed-schema get_recipe query: "chocolate chip cookies"
@fixed-schema get_api_endpoint query: "payment processing API"
@fixed-schema get_article_summary query: "quantum computing trends"
@fixed-schema get_book_review query: "1984 by George Orwell"
@fixed-schema get_movie_review query: "The Matrix"
@fixed-schema get_person_profile query: "Ada Lovelace"
@fixed-schema get_sports_stats query: "LeBron James 2023 season"
@fixed-schema get_troubleshooting_guide query: "Docker container not starting"
```

**Utility tools**:
```
@fixed-schema list_available_schemas
@fixed-schema add_schema schema_name: "news_article" schema_definition: "{\"type\": \"object\", \"properties\": {\"headline\": {\"type\": \"string\"}, \"summary\": {\"type\": \"string\"}}}" description: "News article analysis"
```

## Tips for Best Results

1. **Be specific in your queries** to get more accurate structured responses
2. **Choose the appropriate tool** for your use case - each schema is optimized for different domains
3. **Use the `query` parameter** - all schema-based tools accept a single query parameter
4. **Explore available schemas** using `list_available_schemas` to discover all 10 current tools
5. **Add custom schemas** using `add_schema` for specialized use cases (requires server restart)

## Current Schema Inventory (10 Total)

**Original Schemas**: api_endpoint, article_summary, movie_review, person_profile, product_info, recipe, troubleshooting_guide

**Added Schemas**: book_review, sports_stats, weather_report

**Utility Tools**: list_available_schemas, add_schema

## Architecture Benefits

- **Dynamic & Extensible**: Add unlimited schemas without code changes
- **Consistent Interface**: All schema tools use the same `query` parameter
- **Custom AI Behavior**: Each schema can have specialized system prompts
- **Persistent Schema Addition**: `add_schema` creates permanent files (restart required)
- **Schema Discovery**: Built-in tools to explore available schemas
- **File-Based Configuration**: All schemas stored as JSON files for easy management

## Adding New Schemas

The `add_schema` tool creates persistent schema files but requires a restart:

1. **Call the tool**: Provide schema name, definition, description, and optional system prompt
2. **File created**: Schema saved to `test_config/schemas/{name}.json`
3. **Restart required**: MCP server must be restarted to load the new tool
4. **Tool available**: New `get_{schema_name}` tool becomes fully functional

**Important**: This is not true runtime addition - the server must be restarted for new schemas to become available.

## Note on AWS Integration

The server uses AWS Bedrock Claude for generating responses when AWS credentials are available. If AWS credentials are not configured, the server will automatically fall back to mock responses that still match the schema structure. Each schema can have a custom system prompt to specialize Claude's behavior for that domain.