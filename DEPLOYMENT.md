# Finjo DinarX Platform - Deployment Configuration

## Environment Setup

### Backend Configuration
- **Database**: MongoDB service at `mongodb://mongodb:27017/finjo_db`
- **JWT Secret**: Production-grade secret key for authentication
- **Health Check**: Available at `/health` endpoint

### Frontend Configuration
- **Backend URL**: Configured to use deployment URL from environment
- **API Prefix**: All API calls use `/api` prefix for proper routing

## Database Migration

The platform includes automatic database migration on startup:
- Converts legacy `stablecoin_balance` fields to `dinarx_balance`
- Maintains backward compatibility during migration
- Logs migration progress and results

## Health Monitoring

### Health Check Endpoint
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "service": "Finjo DinarX Platform",
  "database": {
    "connected": true,
    "name": "finjo_db",
    "collections": 8
  },
  "timestamp": "2025-01-18T14:30:00Z"
}
```

## Service Architecture

```
Frontend (React) → Backend (FastAPI) → MongoDB
      ↓                    ↓              ↓
   Port 3000           Port 8001      Port 27017
```

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://mongodb:27017/finjo_db
JWT_SECRET_KEY=finjo-production-secret-key-2025
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-deployment-url.preview.emergentagent.com
```

## Deployment Features

✅ **Database Migration**: Automatic on startup
✅ **Health Monitoring**: Real-time health checks
✅ **Error Handling**: Graceful degradation
✅ **Security**: Production-grade JWT configuration
✅ **Logging**: Comprehensive startup and runtime logging
✅ **Backward Compatibility**: Handles legacy data structures

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MongoDB service is running
   - Verify MONGO_URL environment variable
   - Check health endpoint: `/health`

2. **Migration Errors**
   - Check backend logs for migration status
   - Verify database permissions
   - Ensure MongoDB is accessible

3. **API Errors**
   - Verify backend URL in frontend environment
   - Check CORS configuration
   - Validate JWT secret configuration

### Log Monitoring

Check backend logs for:
- ✅ Database connection successful
- ✅ Migration completed
- ✅ Startup initialization complete

## Production Readiness

The platform is configured for production deployment with:
- **Robust Database Connection**: Handles connection failures gracefully
- **Automatic Migration**: Ensures data consistency
- **Health Monitoring**: Real-time service status
- **Security**: Production-grade authentication
- **Error Handling**: Comprehensive error management
- **Logging**: Detailed operational logs