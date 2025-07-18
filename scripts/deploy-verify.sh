#!/bin/bash

# Finjo DinarX Platform Deployment Verification Script

echo "🚀 Finjo DinarX Platform Deployment Verification"
echo "================================================="

# Check if services are running
echo -e "\n📊 Checking Service Status:"
sudo supervisorctl status

# Check health endpoint
echo -e "\n🏥 Testing Health Check:"
curl -s http://localhost:8001/health | jq .

# Check database connection
echo -e "\n🗄️ Testing Database Connection:"
python3 -c "
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_db():
    try:
        mongo_url = os.getenv('MONGO_URL', 'mongodb://mongodb:27017/finjo_db')
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database('finjo_db')
        collections = await db.list_collection_names()
        print(f'✅ Database connected: {len(collections)} collections')
        client.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"

# Check frontend build
echo -e "\n🌐 Testing Frontend:"
curl -s http://localhost:3000 | head -20

# Check backend API
echo -e "\n🔧 Testing Backend API:"
curl -s http://localhost:8001/api/health || curl -s http://localhost:8001/health

echo -e "\n✅ Deployment verification complete!"
echo "📋 Next steps:"
echo "   1. Test user registration at /register"
echo "   2. Test login at /login"
echo "   3. Test dashboard functionality"
echo "   4. Monitor logs with: tail -f /var/log/supervisor/backend.out.log"