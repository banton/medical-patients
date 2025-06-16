# Timeline Viewer Deployment Guide

This guide covers deploying the React Timeline Viewer to DigitalOcean at viewer.milmed.tech.

## Overview

The Timeline Viewer is a standalone React application that visualizes patient movement through medical facilities. It can be deployed independently from the main application.

## Deployment Options

### Option 1: DigitalOcean App Platform (Recommended)

App Platform provides a fully managed static site hosting solution with automatic SSL, CDN, and GitHub integration.

#### Prerequisites
- DigitalOcean account with App Platform access
- Domain configured in DigitalOcean (viewer.milmed.tech)
- doctl CLI installed and authenticated

#### Deployment Steps

1. **Review the App Spec**:
   ```yaml
   # timeline-viewer-app-spec.yaml
   name: medical-timeline-viewer
   region: nyc
   domains:
     - domain: viewer.milmed.tech
       type: PRIMARY
   ```

2. **Deploy using the script**:
   ```bash
   ./scripts/deploy-timeline-viewer.sh
   ```

3. **Or deploy manually**:
   ```bash
   # Create new app
   doctl apps create --spec timeline-viewer-app-spec.yaml

   # Update existing app
   doctl apps update <app-id> --spec timeline-viewer-app-spec.yaml
   ```

4. **Configure DNS** (if not already done):
   - Add an A record for viewer.milmed.tech pointing to the App Platform IP
   - Or use DigitalOcean's DNS management

### Option 2: Docker Deployment on Droplet

For deployment on an existing Droplet or VPS.

#### Build and Deploy

1. **Build the Docker image**:
   ```bash
   cd patient-timeline-viewer
   docker build -f Dockerfile.prod -t timeline-viewer:latest .
   ```

2. **Run on Droplet**:
   ```bash
   docker run -d \
     --name timeline-viewer \
     -p 3000:80 \
     --restart unless-stopped \
     timeline-viewer:latest
   ```

3. **Configure reverse proxy** (nginx example):
   ```nginx
   server {
       listen 80;
       server_name viewer.milmed.tech;

       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Option 3: GitHub Actions Automated Deployment

The repository includes a GitHub Actions workflow for automated deployment.

#### Setup

1. **Add GitHub Secrets**:
   - `DIGITALOCEAN_ACCESS_TOKEN`: Your DigitalOcean API token

2. **Enable GitHub Actions**:
   - The workflow triggers on pushes to `main` that modify the timeline viewer
   - Or trigger manually from the Actions tab

## Configuration

### Environment Variables

The timeline viewer supports these environment variables:

- `VITE_API_URL`: Base URL for the API (default: https://api.milmed.tech)

### Build-time Configuration

Update `vite.config.ts` for build optimizations:

```typescript
export default defineConfig({
  base: '/', // For root domain deployment
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable in production
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'animation': ['framer-motion']
        }
      }
    }
  }
});
```

## Monitoring and Maintenance

### App Platform Monitoring

```bash
# View app status
doctl apps list

# View deployment logs
doctl apps logs medical-timeline-viewer

# View app metrics
doctl apps metrics get <app-id> --resource-type app
```

### Docker Monitoring

```bash
# View container logs
docker logs timeline-viewer

# Check container status
docker ps -a | grep timeline-viewer

# View resource usage
docker stats timeline-viewer
```

## SSL/TLS Configuration

### App Platform
- SSL is automatically provisioned and managed
- Force HTTPS is enabled by default

### Manual Deployment
Use Certbot for Let's Encrypt certificates:

```bash
sudo certbot --nginx -d viewer.milmed.tech
```

## Performance Optimization

### CDN Configuration
App Platform includes CDN by default. For manual deployments, consider:
- Cloudflare
- DigitalOcean Spaces CDN

### Asset Optimization
The build process includes:
- Code splitting
- Tree shaking
- Minification
- Gzip compression

## Troubleshooting

### Common Issues

1. **Build Failures**:
   ```bash
   # Check Node version
   node --version  # Should be 18+
   
   # Clear cache and rebuild
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

2. **404 Errors on Routes**:
   - Ensure nginx/server is configured for SPA routing
   - All routes should serve index.html

3. **CORS Issues**:
   - Verify CORS settings in app spec
   - Check API allows viewer.milmed.tech origin

### Debug Commands

```bash
# Test build locally
cd patient-timeline-viewer
npm run build
npm run preview

# Check App Platform deployment
doctl apps get medical-timeline-viewer
doctl apps list-deployments <app-id>

# View deployment details
doctl apps get-deployment <app-id> <deployment-id>
```

## Rollback Procedures

### App Platform
```bash
# List deployments
doctl apps list-deployments <app-id>

# Rollback to previous deployment
doctl apps create-deployment <app-id> --rollback <deployment-id>
```

### Docker
```bash
# Tag current version before updating
docker tag timeline-viewer:latest timeline-viewer:backup

# Rollback if needed
docker stop timeline-viewer
docker rm timeline-viewer
docker run -d --name timeline-viewer -p 3000:80 timeline-viewer:backup
```

## Security Considerations

1. **Content Security Policy**: Configure in nginx.conf
2. **CORS**: Limit to known origins
3. **API Keys**: Never expose in frontend code
4. **Updates**: Keep dependencies updated

## Cost Optimization

### App Platform
- Static sites: $0/month for 3 sites
- Bandwidth: 100 GB/month free
- Build minutes: 2500/month free

### Droplet
- Use smallest droplet size (512MB RAM sufficient)
- Enable monitoring for resource optimization

## Future Enhancements

1. **PWA Support**: Add service worker for offline capability
2. **Analytics**: Integrate privacy-friendly analytics
3. **A/B Testing**: Implement feature flags
4. **Multi-region**: Deploy to multiple regions for lower latency