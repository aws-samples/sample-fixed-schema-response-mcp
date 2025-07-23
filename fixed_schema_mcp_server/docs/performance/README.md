# Performance Tuning Guide

## Introduction

This guide provides recommendations for optimizing the performance of the Fixed Schema Response MCP Server. Performance tuning is essential for handling high request volumes, reducing latency, and ensuring efficient resource utilization.

## Performance Metrics

Before tuning, it's important to understand the key performance metrics:

1. **Throughput**: Number of requests processed per second
2. **Latency**: Time taken to process a request
3. **Resource Utilization**: CPU, memory, and network usage
4. **Success Rate**: Percentage of requests that complete successfully

## Configuration Recommendations

### Server Configuration

#### Concurrent Requests

Configure the maximum number of concurrent requests based on your hardware:

```json
{
  "server": {
    "max_concurrent_requests": 10,
    "queue_size": 100
  }
}
```

Guidelines:
- For each CPU core, allow 2-3 concurrent requests
- Set queue size to handle expected request bursts

#### Worker Processes

For multi-core systems, configure multiple worker processes:

```json
{
  "server": {
    "workers": 4
  }
}
```

Guidelines:
- Set workers equal to the number of CPU cores
- For memory-intensive workloads, use fewer workers

### Model Configuration

#### Connection Pooling

Enable connection pooling to reuse connections to the model API:

```json
{
  "model": {
    "connection_pool": {
      "max_connections": 10,
      "min_connections": 2,
      "max_idle_time": 300
    }
  }
}
```

Guidelines:
- Set max_connections to match max_concurrent_requests
- Keep min_connections > 0 to maintain warm connections
- Adjust max_idle_time based on request patterns

#### Request Batching

Enable request batching to combine multiple requests into a single API call:

```json
{
  "model": {
    "batching": {
      "enabled": true,
      "max_batch_size": 5,
      "max_batch_wait_time": 0.1
    }
  }
}
```

Guidelines:
- Only enable if your model provider supports batching
- Set max_batch_size based on model capabilities
- Keep max_batch_wait_time low to avoid adding latency

### Caching Configuration

Enable response caching to avoid redundant model calls:

```json
{
  "caching": {
    "enabled": true,
    "cache_size": 1000,
    "ttl": 3600,
    "similarity_threshold": 0.95
  }
}
```

Guidelines:
- Enable for use cases with repetitive queries
- Adjust cache_size based on available memory
- Set TTL (time-to-live) based on how frequently responses change
- Tune similarity_threshold to balance cache hits vs. accuracy

### Schema Configuration

Optimize schema validation for performance:

```json
{
  "schemas": {
    "validation": {
      "cache_compiled_schemas": true,
      "fast_validation": true
    }
  }
}
```

Guidelines:
- Always cache compiled schemas for better performance
- Enable fast validation for high-throughput scenarios
- For critical accuracy, disable fast validation

## Hardware Recommendations

### CPU

- **Minimum**: 2 CPU cores
- **Recommended**: 4+ CPU cores
- **High-volume**: 8+ CPU cores

The server is CPU-bound during schema validation and response processing.

### Memory

- **Minimum**: 2GB RAM
- **Recommended**: 4GB RAM
- **High-volume**: 8GB+ RAM

Memory usage increases with concurrent requests, connection pooling, and caching.

### Network

- **Bandwidth**: 10+ Mbps
- **Latency**: Lower is better, especially to model API endpoints

Network performance is critical when communicating with external model APIs.

### Disk

- **Speed**: SSD recommended for log writing
- **Space**: 1GB+ for logs and cache

Disk performance is less critical unless extensive logging is enabled.

## Optimization Techniques

### Request Queuing

Implement request queuing to handle traffic spikes:

```json
{
  "server": {
    "queue": {
      "enabled": true,
      "max_size": 1000,
      "timeout": 30
    }
  }
}
```

Benefits:
- Prevents server overload during traffic spikes
- Ensures fair request processing
- Improves overall stability

### Rate Limiting

Configure rate limiting to prevent abuse:

```json
{
  "server": {
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60,
      "requests_per_day": 1000
    }
  }
}
```

Benefits:
- Prevents resource exhaustion
- Ensures fair resource allocation
- Reduces costs for pay-per-request model APIs

### Response Streaming

Enable response streaming for faster time-to-first-byte:

```json
{
  "server": {
    "streaming": {
      "enabled": true,
      "chunk_size": 1024
    }
  }
}
```

Benefits:
- Reduces perceived latency
- Improves user experience
- Better handles long responses

### Schema Optimization

Optimize schemas for better performance:

1. **Simplify schemas**: Remove unnecessary complexity
2. **Limit nesting depth**: Deep nesting slows validation
3. **Use efficient validation rules**: Avoid complex patterns and custom formats

### Model Parameter Tuning

Optimize model parameters for performance:

```json
{
  "model": {
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 500
    }
  }
}
```

Guidelines:
- Lower temperature for more consistent responses
- Limit max_tokens to reduce generation time
- Adjust top_p for a balance of creativity and speed

## Benchmarking Guide

### Setting Up Benchmarks

1. **Define test scenarios**:
   - Low volume (1 request/second)
   - Medium volume (10 requests/second)
   - High volume (50+ requests/second)

2. **Prepare test data**:
   - Create a variety of realistic queries
   - Include edge cases and complex queries

3. **Set up monitoring**:
   - Track server metrics (CPU, memory, requests/second)
   - Measure response times
   - Record error rates

### Benchmarking Tools

1. **Apache Benchmark (ab)**:
   ```bash
   ab -n 1000 -c 10 -p request.json -T application/json http://localhost:8000/generate
   ```

2. **wrk**:
   ```bash
   wrk -t4 -c50 -d30s -s request.lua http://localhost:8000/generate
   ```

3. **Locust**:
   Create a locustfile.py for more complex scenarios:
   ```python
   from locust import HttpUser, task, between

   class MCPUser(HttpUser):
       wait_time = between(1, 5)
       
       @task
       def generate_response(self):
           self.client.post("/generate", json={
               "query": "Tell me about the latest iPhone",
               "schema": "product_info"
           })
   ```

### Analyzing Results

1. **Throughput analysis**:
   - Measure requests per second
   - Identify throughput bottlenecks

2. **Latency analysis**:
   - Measure average, median, p95, and p99 latencies
   - Identify latency spikes

3. **Error rate analysis**:
   - Track percentage of failed requests
   - Categorize errors by type

4. **Resource utilization**:
   - Monitor CPU, memory, and network usage
   - Identify resource bottlenecks

## Performance Optimization Examples

### Example 1: High-Throughput Configuration

For applications requiring high throughput:

```json
{
  "server": {
    "workers": 8,
    "max_concurrent_requests": 20,
    "queue_size": 200
  },
  "model": {
    "connection_pool": {
      "max_connections": 20,
      "min_connections": 5
    },
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 300
    }
  },
  "caching": {
    "enabled": true,
    "cache_size": 5000,
    "ttl": 3600
  },
  "schemas": {
    "validation": {
      "cache_compiled_schemas": true,
      "fast_validation": true
    }
  }
}
```

### Example 2: Low-Latency Configuration

For applications requiring low latency:

```json
{
  "server": {
    "workers": 4,
    "max_concurrent_requests": 10,
    "streaming": {
      "enabled": true,
      "chunk_size": 512
    }
  },
  "model": {
    "connection_pool": {
      "max_connections": 10,
      "min_connections": 5,
      "max_idle_time": 600
    },
    "parameters": {
      "temperature": 0.3,
      "max_tokens": 200
    }
  },
  "caching": {
    "enabled": true,
    "cache_size": 2000,
    "ttl": 1800,
    "similarity_threshold": 0.98
  }
}
```

### Example 3: Balanced Configuration

For applications requiring a balance of throughput and latency:

```json
{
  "server": {
    "workers": 4,
    "max_concurrent_requests": 15,
    "queue_size": 100,
    "streaming": {
      "enabled": true
    }
  },
  "model": {
    "connection_pool": {
      "max_connections": 15,
      "min_connections": 3
    },
    "parameters": {
      "temperature": 0.5,
      "max_tokens": 500
    }
  },
  "caching": {
    "enabled": true,
    "cache_size": 3000,
    "ttl": 2400
  }
}
```

## Monitoring and Profiling

### Enabling Metrics

Enable metrics collection for monitoring:

```json
{
  "server": {
    "metrics": {
      "enabled": true,
      "port": 9090
    }
  }
}
```

### Key Metrics to Monitor

1. **Request metrics**:
   - Requests per second
   - Request latency (average, p95, p99)
   - Queue length
   - Error rate

2. **Model metrics**:
   - Model API latency
   - Token usage
   - API errors
   - Connection pool utilization

3. **Cache metrics**:
   - Cache hit rate
   - Cache size
   - Cache evictions

4. **System metrics**:
   - CPU usage
   - Memory usage
   - Network I/O
   - Disk I/O

### Profiling

For detailed performance analysis, enable profiling:

```json
{
  "server": {
    "profiling": {
      "enabled": true,
      "interval": 60
    }
  }
}
```

Access profiling data at `http://localhost:8000/debug/pprof`

## Conclusion

Performance tuning is an iterative process. Start with the recommended configurations, benchmark your application, identify bottlenecks, and make targeted optimizations. Monitor performance continuously and adjust configurations as your usage patterns evolve.

Remember that performance tuning involves trade-offs. Optimizing for throughput may increase latency, while optimizing for low latency may reduce throughput. Choose configurations that align with your application's specific requirements.