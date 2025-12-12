# 🚀 Deployment Guide

This guide covers deploying the AI Project Synthesizer in various environments, from development to production.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Security Considerations](#security-considerations)

---

## 🎯 Deployment Options

### Development Environment
- Local development with virtual environment
- Docker Compose for local testing
- Hot-reload enabled for rapid iteration

### Staging Environment
- Docker containers in cloud VM
- Production-like configuration
- Integration testing environment

### Production Environment
- Kubernetes cluster for scalability
- Load balancer and auto-scaling
- High availability and disaster recovery

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose

1. **Clone and prepare:**
```bash
git clone https://github.com/yourusername/ai-project-synthesizer.git
cd ai-project-synthesizer
cp .env.example .env
# Edit .env with your configuration
```

2. **Deploy with Docker Compose:**
```bash
docker-compose up -d
```

3. **Verify deployment:**
```bash
docker-compose ps
curl http://localhost:8000/health
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: ai-synthesizer:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: ai-synthesizer:worker
    restart: unless-stopped
    environment:
      - ENV=production
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    deploy:
      replicas: 3

  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile Optimization

Create optimized `Dockerfile.prod`:

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "src.server"]
```

---

## ☸️ Kubernetes Deployment

### Namespace and ConfigMaps

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-synthesizer
```

Create `k8s/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-synthesizer-config
  namespace: ai-synthesizer
data:
  ENV: "production"
  LOG_LEVEL: "INFO"
  REDIS_URL: "redis://redis-service:6379"
```

### Secrets Management

Create `k8s/secrets.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-synthesizer-secrets
  namespace: ai-synthesizer
type: Opaque
data:
  DATABASE_URL: <base64-encoded-url>
  OPENAI_API_KEY: <base64-encoded-key>
  ANTHROPIC_API_KEY: <base64-encoded-key>
```

### Deployment Configuration

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-synthesizer-api
  namespace: ai-synthesizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-synthesizer-api
  template:
    metadata:
      labels:
        app: ai-synthesizer-api
    spec:
      containers:
      - name: api
        image: ai-synthesizer:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-synthesizer-config
        - secretRef:
            name: ai-synthesizer-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-synthesizer-worker
  namespace: ai-synthesizer
spec:
  replicas: 5
  selector:
    matchLabels:
      app: ai-synthesizer-worker
  template:
    metadata:
      labels:
        app: ai-synthesizer-worker
    spec:
      containers:
      - name: worker
        image: ai-synthesizer:worker
        envFrom:
        - configMapRef:
            name: ai-synthesizer-config
        - secretRef:
            name: ai-synthesizer-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service and Load Balancer

Create `k8s/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-synthesizer-service
  namespace: ai-synthesizer
spec:
  selector:
    app: ai-synthesizer-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-synthesizer-ingress
  namespace: ai-synthesizer
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.ai-synthesizer.dev
    secretName: ai-synthesizer-tls
  rules:
  - host: api.ai-synthesizer.dev
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-synthesizer-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler

Create `k8s/hpa.yaml`:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-synthesizer-hpa
  namespace: ai-synthesizer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-synthesizer-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get all -n ai-synthesizer

# View logs
kubectl logs -f deployment/ai-synthesizer-api -n ai-synthesizer

# Scale deployment
kubectl scale deployment ai-synthesizer-api --replicas=5 -n ai-synthesizer
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### Using ECS

1. **Create ECR repository:**
```bash
aws ecr create-repository --repository-name ai-synthesizer
```

2. **Build and push image:**
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com
docker build -t ai-synthesizer .
docker tag ai-synthesizer:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/ai-synthesizer:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/ai-synthesizer:latest
```

3. **Create ECS task definition:**
```json
{
  "family": "ai-synthesizer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ai-synthesizer",
      "image": "<account-id>.dkr.ecr.us-west-2.amazonaws.com/ai-synthesizer:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:<account-id>:secret:ai-synthesizer/db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-synthesizer",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Using EKS

```bash
# Create EKS cluster
eksctl create cluster \
  --name ai-synthesizer \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed

# Deploy using the Kubernetes manifests from previous section
kubectl apply -f k8s/
```

### Google Cloud Deployment

#### Using Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-synthesizer
gcloud run deploy ai-synthesizer \
  --image gcr.io/PROJECT_ID/ai-synthesizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 100
```

#### Using GKE

```bash
# Create GKE cluster
gcloud container clusters create ai-synthesizer \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --region=us-central1

# Get credentials
gcloud container clusters get-credentials ai-synthesizer --region=us-central1

# Deploy
kubectl apply -f k8s/
```

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name ai-synthesizer-rg --location eastus

# Deploy container
az container create \
  --resource-group ai-synthesizer-rg \
  --name ai-synthesizer \
  --image ai-synthesizer:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables ENV=production
```

---

## ⚙️ Environment Configuration

### Production Environment Variables

Create `.env.production`:

```env
# Environment
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Cache
REDIS_URL=redis://host:6379/0
CACHE_TTL=3600

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET=your-jwt-secret
CORS_ORIGINS=https://app.ai-synthesizer.dev

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...

# Monitoring
SENTRY_DSN=https://...
PROMETHEUS_ENABLED=true

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
REQUEST_TIMEOUT=30
```

### Configuration Management

```python
# src/core/config.py
from pydantic import BaseSettings
from typing import Optional

class ProductionConfig(BaseSettings):
    env: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    database_url: str
    db_pool_size: int = 20
    db_max_overflow: int = 30
    
    redis_url: str
    cache_ttl: int = 3600
    
    secret_key: str
    jwt_secret: str
    cors_origins: str
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = False
    
    worker_processes: int = 4
    max_connections: int = 1000
    request_timeout: int = 30
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False
```

---

## 📊 Monitoring & Maintenance

### Prometheus Monitoring

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-synthesizer'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Grafana Dashboard

Key metrics to monitor:
- Request rate and latency
- Error rates by endpoint
- Memory and CPU usage
- Database connection pool
- Cache hit rates
- AI API usage and costs
- Queue depth and processing time

### Log Aggregation

Using ELK stack:
```yaml
# logging/elasticsearch.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    ports:
      - "5044:5044"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

### Health Checks

Implement comprehensive health checks:
```python
# src/core/health.py
from fastapi import APIRouter
from sqlalchemy import text
from redis import Redis

router = APIRouter()

@router.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "ai_providers": await check_ai_providers(),
    }
    
    status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }

async def check_database():
    try:
        await db.execute(text("SELECT 1"))
        return "healthy"
    except:
        return "unhealthy"

async def check_redis():
    try:
        redis_client.ping()
        return "healthy"
    except:
        return "unhealthy"
```

---

## 🔒 Security Considerations

### Network Security

1. **Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw enable
```

2. **Network Policies in Kubernetes:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-synthesizer-netpol
  namespace: ai-synthesizer
spec:
  podSelector:
    matchLabels:
      app: ai-synthesizer-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### Secrets Management

1. **Using Kubernetes Secrets:**
```bash
# Create secret from file
kubectl create secret generic ai-keys \
  --from-file=openai=./openai.key \
  --from-file=anthropic=./anthropic.key \
  -n ai-synthesizer
```

2. **Using AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name ai-synthesizer/keys \
  --secret-string '{"openai":"sk-...","anthropic":"sk-ant-..."}'
```

### SSL/TLS Configuration

Nginx configuration for HTTPS:
```nginx
server {
    listen 443 ssl http2;
    server_name api.ai-synthesizer.dev;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: pytest --cov=src tests/
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: |
        docker build -t ai-synthesizer:${{ github.sha }} .
        docker tag ai-synthesizer:${{ github.sha }} ai-synthesizer:latest
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push ai-synthesizer:${{ github.sha }}
        docker push ai-synthesizer:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Kubernetes
      run: |
        echo ${{ secrets.KUBECONFIG }} | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl set image deployment/ai-synthesizer-api api=ai-synthesizer:${{ github.sha }} -n ai-synthesizer
        kubectl rollout status deployment/ai-synthesizer-api -n ai-synthesizer
```

---

## 📈 Scaling Strategies

### Vertical Scaling

Increase resources per instance:
```yaml
# Kubernetes
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Horizontal Scaling

Add more instances:
```bash
# Docker Compose
docker-compose up --scale worker=5

# Kubernetes
kubectl scale deployment ai-synthesizer-api --replicas=10
```

### Auto Scaling

Based on metrics:
```yaml
# Kubernetes HPA
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
- type: Pods
  pods:
    metric:
      name: requests_per_second
    target:
      type: AverageValue
      averageValue: "100"
```

---

## 🛠️ Maintenance Tasks

### Regular Backups

```bash
# Database backup
kubectl exec -n ai-synthesizer deployment/postgres -- pg_dump -U user db > backup.sql

# Redis backup
kubectl exec -n ai-synthesizer deployment/redis -- redis-cli BGSAVE
```

### Log Rotation

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "3"
```

### Updates and Patches

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Kubernetes rolling update
kubectl set image deployment/ai-synthesizer-api api=ai-synthesizer:v1.2.0
```

---

## 📝 Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Rollback plan ready

### Post-deployment
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Load testing performed
- [ ] User acceptance testing
- [ ] Documentation verified
- [ ] Team training completed

---

## 🆘 Troubleshooting Deployment

### Common Issues

1. **Pods not starting:**
   - Check resource limits
   - Verify image pull secrets
   - Review pod logs: `kubectl logs -f pod/name`

2. **High memory usage:**
   - Check for memory leaks
   - Adjust resource limits
   - Implement memory profiling

3. **Database connection issues:**
   - Verify connection string
   - Check network policies
   - Review pool settings

4. **Slow response times:**
   - Check resource utilization
   - Review query performance
   - Implement caching

### Debug Commands

```bash
# Kubernetes
kubectl describe pod <pod-name> -n ai-synthesizer
kubectl logs -f deployment/<deployment-name> -n ai-synthesizer
kubectl exec -it <pod-name> -n ai-synthesizer -- bash

# Docker
docker-compose logs -f
docker exec -it <container-name> bash
docker stats
```

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS Deployment Guide](https://docs.aws.amazon.com/)
- [Google Cloud Deployment](https://cloud.google.com/docs)
- [Azure Deployment](https://docs.microsoft.com/azure/)

---

Need help with deployment? [Contact our support team](mailto:support@ai-synthesizer.dev) or [open an issue](https://github.com/yourusername/ai-project-synthesizer/issues).
