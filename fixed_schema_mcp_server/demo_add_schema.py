#!/usr/bin/env python3
"""
Demonstration of adding a new schema dynamically to the generic MCP server.
"""

import json

# Example: Adding a new "movie_review" schema
new_schema = {
    "name": "movie_review",
    "description": "Schema for movie review information",
    "schema": {
        "type": "object",
        "required": ["title", "rating", "review"],
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the movie"
            },
            "director": {
                "type": "string", 
                "description": "The director of the movie"
            },
            "year": {
                "type": "integer",
                "description": "Release year of the movie"
            },
            "genre": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Movie genres"
            },
            "rating": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "Rating out of 10"
            },
            "review": {
                "type": "string",
                "description": "Detailed review text"
            },
            "pros": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Positive aspects of the movie"
            },
            "cons": {
                "type": "array", 
                "items": {"type": "string"},
                "description": "Negative aspects of the movie"
            },
            "recommendation": {
                "type": "string",
                "enum": ["highly_recommended", "recommended", "neutral", "not_recommended"],
                "description": "Overall recommendation"
            }
        }
    },
    "system_prompt": "You are a professional movie critic with expertise in cinema. Provide thoughtful, balanced movie reviews that consider plot, acting, direction, cinematography, and overall entertainment value."
}

def create_schema_file():
    """Create the new schema file."""
    with open("test_config/schemas/movie_review.json", "w") as f:
        json.dump(new_schema, f, indent=2)
    
    print("✅ Created movie_review.json schema file")
    print("🔄 Restart the server to load the new schema")
    print("🛠️  New tool will be available: get_movie_review(query: str)")

def show_runtime_addition():
    """Show how to add schema at runtime using the add_schema tool."""
    print("\n" + "="*60)
    print("RUNTIME SCHEMA ADDITION EXAMPLE")
    print("="*60)
    
    print("You can also add schemas at runtime using the add_schema tool:")
    print()
    print("add_schema(")
    print(f'    schema_name="movie_review",')
    print(f'    schema_definition=\'{json.dumps(new_schema["schema"])}\',')
    print(f'    description="{new_schema["description"]}",')
    print(f'    system_prompt="{new_schema["system_prompt"][:50]}..."')
    print(")")
    print()
    print("This will immediately create the get_movie_review tool without restarting!")

if __name__ == "__main__":
    print("🎬 Adding Movie Review Schema to Generic MCP Server")
    print("="*60)
    
    create_schema_file()
    show_runtime_addition()
    
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    print("Once loaded, you can use the new tool like this:")
    print()
    print('get_movie_review("The Matrix")')
    print('get_movie_review("latest Marvel movie")')
    print('get_movie_review("Citizen Kane classic film analysis")')
    print()
    print("The tool will return structured movie review data matching the schema!")