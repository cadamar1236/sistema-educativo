# Azure App Service Deployment Guide

## Quick Start (10-15 seconds)

Use the ultra-fast startup script for immediate deployment:

```bash
# In Azure App Service Startup Command:
bash azure-quick-start.sh
```

This provides:
- ✅ 10-15 second startup time
- ✅ Minimal resource usage
- ✅ Preloaded application
- ✅ 2 optimized workers

## Full Deployment

### 1. Azure Portal Configuration

#### App Service Plan
- **Tier**: B1 or higher (B2 recommended)
- **Operating System**: Linux
- **Runtime Stack**: Python 3.11

#### Application Settings
```
WEBSITE_PORT=8000
PYTHON_VERSION=3.11
SCM_DO_BUILD_DURING_DEPLOYMENT=true
WORKERS=4
ENABLE_ORYX_BUILD=true
```

#### Startup Command
```bash
# Option 1: Ultra-fast (10-15s)
bash azure-quick-start.sh

# Option 2: Full startup with dependencies
bash azure-startup.sh

# Option 3: Direct Gunicorn
gunicorn src.main_simple:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 --preload
```

### 2. Deployment Methods

#### Azure CLI Deployment
```bash
# Login to Azure
az login

# Create resource group
az group create --name julia-ai-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name julia-ai-plan \
  --resource-group julia-ai-rg \
  --sku B2 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group julia-ai-rg \
  --plan julia-ai-plan \
  --name julia-ai-app \
  --runtime "PYTHON:3.11"

# Configure startup
az webapp config set \
  --resource-group julia-ai-rg \
  --name julia-ai-app \
  --startup-file "bash azure-quick-start.sh"

# Deploy code
az webapp deployment source config-local-git \
  --name julia-ai-app \
  --resource-group julia-ai-rg

# Push to Azure
git remote add azure <deployment-url>
git push azure main
```

#### GitHub Actions Deployment
```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-azure.txt
    
    - name: Deploy to Azure
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'julia-ai-app'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        startup-command: 'bash azure-quick-start.sh'
```

### 3. Performance Optimization

#### Startup Time Optimization
| Script | Startup Time | Workers | Memory | Best For |
|--------|-------------|---------|---------|----------|
| azure-quick-start.sh | 10-15s | 2 | Low | Production |
| azure-startup.sh | 30-45s | 4 | Medium | Full features |
| Direct uvicorn | 5-10s | 1 | Minimal | Development |

#### Memory Optimization
```python
# In gunicorn_config.py
workers = 2  # Reduce workers
max_requests = 1000  # Restart workers periodically
preload_app = True  # Share memory between workers
```

#### Database Optimization
- Use Azure Cosmos DB for vector storage
- Enable connection pooling
- Use Redis Cache for session management

### 4. Monitoring

#### Application Insights
```python
# Add to main_simple.py
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string="<your-connection-string>"
)
```

#### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }
```

### 5. Troubleshooting

#### Slow Startup
1. Use `azure-quick-start.sh` instead of full startup
2. Reduce worker count to 2
3. Enable preloading with `--preload`
4. Use B2 or higher tier

#### Memory Issues
1. Set `MAX_REQUESTS=1000` to restart workers
2. Reduce worker count
3. Use connection pooling
4. Scale up to higher tier

#### Timeout Errors
1. Increase timeout in gunicorn config
2. Use async endpoints
3. Implement background tasks
4. Enable Always On in Azure

### 6. Cost Optimization

#### Recommendations
- **Development**: B1 tier ($13/month)
- **Production**: B2 tier ($52/month)
- **High Traffic**: S2 tier ($200/month)

#### Auto-scaling Rules
```json
{
  "rules": [
    {
      "metric": "CpuPercentage",
      "threshold": 70,
      "scaleAction": "Increase",
      "instances": 1
    },
    {
      "metric": "MemoryPercentage", 
      "threshold": 80,
      "scaleAction": "Increase",
      "instances": 1
    }
  ]
}
```

### 7. Security

#### Environment Variables
Store sensitive data in Azure Key Vault:
```bash
az keyvault secret set \
  --vault-name julia-ai-vault \
  --name "OPENAI-API-KEY" \
  --value "your-api-key"
```

#### Network Security
- Enable HTTPS only
- Configure CORS properly
- Use Azure Front Door for DDoS protection
- Enable Web Application Firewall

### 8. File Upload Configuration

#### Azure Storage Integration
```python
# For large file uploads
from azure.storage.blob import BlobServiceClient

blob_service = BlobServiceClient(
    connection_string=os.getenv("AZURE_STORAGE_CONNECTION")
)
```

#### Size Limits
```python
# In main_simple.py
app.add_middleware(
    CORSMiddleware,
    max_upload_size=100 * 1024 * 1024  # 100MB
)
```

## Quick Commands

```bash
# View logs
az webapp log tail --name julia-ai-app --resource-group julia-ai-rg

# Restart app
az webapp restart --name julia-ai-app --resource-group julia-ai-rg

# Scale up
az appservice plan update --name julia-ai-plan --resource-group julia-ai-rg --sku B2

# Check health
curl https://julia-ai-app.azurewebsites.net/health
```

## Support

For issues or questions:
1. Check Azure App Service logs
2. Review Application Insights
3. Test locally with `bash azure-quick-start.sh`
4. Contact Azure Support