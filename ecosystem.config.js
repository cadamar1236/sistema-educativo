module.exports = {
  apps: [
    {
      name: 'julia-backend',
      script: 'gunicorn',
      args: 'src.main_simple:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 --preload',
      interpreter: 'python3',
      env: {
        PORT: 8000,
        PYTHONUNBUFFERED: 1,
        ENVIRONMENT: 'development'
      },
      env_production: {
        PORT: 8000,
        PYTHONUNBUFFERED: 1,
        ENVIRONMENT: 'production',
        WORKERS: 4
      },
      // PM2 specific configurations
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      // Logging
      log_file: './logs/combined.log',
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      // Advanced features
      min_uptime: '10s',
      listen_timeout: 3000,
      kill_timeout: 5000,
      wait_ready: true,
      // Health check
      health_check: {
        interval: 30000,
        timeout: 5000,
        max_consecutive_failures: 3,
        path: '/health'
      }
    },
    {
      name: 'julia-frontend',
      script: 'npm',
      args: 'run dev',
      cwd: './julia-frontend',
      env: {
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000'
      },
      env_production: {
        PORT: 3000,
        NODE_ENV: 'production',
        NEXT_PUBLIC_API_URL: 'https://api.julia-ai.com'
      },
      // PM2 configurations
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      // Logging
      log_file: './logs/frontend-combined.log',
      out_file: './logs/frontend-out.log',
      error_file: './logs/frontend-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ],

  // Deploy configuration
  deploy: {
    production: {
      user: 'azure',
      host: 'julia-ai.azurewebsites.net',
      ref: 'origin/main',
      repo: 'git@github.com:yourusername/julia-ai.git',
      path: '/home/azure/julia-ai',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env production',
      'pre-deploy-local': 'echo "Deploying to production..."'
    },
    development: {
      user: 'dev',
      host: 'localhost',
      ref: 'origin/develop',
      repo: 'git@github.com:yourusername/julia-ai.git',
      path: '/home/dev/julia-ai',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env development',
      'pre-deploy-local': 'echo "Deploying to development..."'
    }
  }
};