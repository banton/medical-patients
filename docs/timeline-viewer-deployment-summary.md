# Timeline Viewer Deployment Summary

## Deployment Details

**Date**: June 16, 2025  
**App Name**: medical-timeline-viewer  
**App ID**: 34692116-878c-4ed8-8a0c-bf388dd11ca9  
**Region**: NYC (New York)  
**Tier**: Starter (Free for static sites)

## URLs

- **Production URL**: https://viewer.milmed.tech (DNS configuring)
- **Default URL**: https://medical-timeline-viewer-6owr2.ondigitalocean.app (active)

## Deployment Configuration

### Build Settings
- **Source**: GitHub - banton/medical-patients
- **Branch**: feature/timeline-viewer-deployment
- **Source Directory**: patient-timeline-viewer
- **Build Command**: `npm ci && npm run build`
- **Output Directory**: dist

### Environment Variables
- `VITE_API_URL`: https://api.milmed.tech

### CORS Configuration
- Allowed Origins: https://api.milmed.tech, https://milmed.tech
- Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed Headers: Content-Type, Authorization

## Build Information

- **Build Time**: ~72 seconds
- **Billable Build Time**: ~21 seconds
- **Buildpacks Used**:
  - Node.js (v0.288.5)
  - Custom Build Command (v0.1.3)
  - Procfile (v0.1.0)

## DNS Configuration

The domain `viewer.milmed.tech` is currently being configured by DigitalOcean App Platform.

### Current Status
- Domain Phase: CONFIGURING
- SSL Certificate: Pending

### Next Steps
1. Wait for automatic DNS configuration (5-10 minutes)
2. SSL certificate will be automatically provisioned
3. Domain will become accessible at https://viewer.milmed.tech

## Monitoring

### Check App Status
```bash
doctl apps get 34692116-878c-4ed8-8a0c-bf388dd11ca9
```

### View Logs
```bash
doctl apps logs 34692116-878c-4ed8-8a0c-bf388dd11ca9
```

### List Deployments
```bash
doctl apps list-deployments 34692116-878c-4ed8-8a0c-bf388dd11ca9
```

## Automatic Deployments

The app is configured for automatic deployments:
- Triggers on push to `feature/timeline-viewer-deployment` branch
- Will need to update to `main` branch after merge

### Update Branch for Production
```bash
doctl apps update 34692116-878c-4ed8-8a0c-bf388dd11ca9 \
  --spec timeline-viewer-app-spec.yaml
```

## Cost

- **Static Sites**: Free (up to 3 static sites)
- **Bandwidth**: 100 GB/month included
- **Build Minutes**: 2,500/month included

Current usage is well within free tier limits.