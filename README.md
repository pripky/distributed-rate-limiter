# Distributed Rate Limiter Service

A low-latency, distributed rate-limiting microservice designed to protect downstream infrastructure from traffic spikes. This system implements an atomic Token Bucket algorithm leveraging a high-performance Redis interface to prevent race conditions across multi-node cluster deployments.

## 🚀 Key Architectural Highlights

* **Atomic Distributed Evaluation:** Utilizes a highly optimized Lua script executed directly inside the Redis kernel to ensure read-and-update tasks are strictly atomic, completely neutralizing concurrency race conditions.
* **In-Memory Caching Tier:** Implements a localized fast-path tracking layer (50ms cache lockout window) that bypasses network hops entirely for highly active malicious clients, consistently preserving sub-2ms lookup latencies.
* **Zero-Downtime Configuration Reloading:** Features an administrative routing engine to dynamically modify and reload capacity limits at runtime without requiring service restarts or dropping active network connections.

## 🛠️ Project Structure

```text
distributed-rate-limiter/
├── main.py          # FastAPI web application, route handling, and middleware integration
├── limiter.py       # Distributed Token Bucket core class and local memory caching layers
└── requirements.txt # Explicit module versions
