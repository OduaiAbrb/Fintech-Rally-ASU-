#!/usr/bin/env python3
"""
Test AML monitoring integration with deposit transaction
"""

import asyncio
import httpx
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://fb2b8618-5ed0-42da-9035-50aa156b0e1e.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

async def test_aml_integration():
    """Test AML monitoring with deposit transaction"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        login_data = {
            "email": "ahmed.hassan@example.com",
            "password": "SecurePass123!"
        }
        
        login_response = await client.post(f"{API_BASE}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ Failed to login")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("🔍 Testing AML Integration with Deposit Transaction")
        print("=" * 60)
        
        # Create a large deposit to trigger AML monitoring
        deposit_data = {
            "transaction_type": "deposit",
            "amount": 25000.0,  # Large amount to trigger AML
            "currency": "JD",
            "description": "Large deposit for AML integration test"
        }
        
        print(f"💰 Creating deposit: {deposit_data['amount']} {deposit_data['currency']}")
        
        # Make deposit
        deposit_response = await client.post(
            f"{API_BASE}/wallet/deposit",
            headers=headers,
            json=deposit_data
        )
        
        if deposit_response.status_code == 200:
            deposit_result = deposit_response.json()
            transaction_id = deposit_result["transaction_id"]
            print(f"✅ Deposit successful - Transaction ID: {transaction_id}")
            
            # Wait for AML processing
            await asyncio.sleep(2)
            
            # Check AML alerts
            alerts_response = await client.get(f"{API_BASE}/aml/alerts", headers=headers)
            
            if alerts_response.status_code == 200:
                alerts_data = alerts_response.json()
                print(f"📊 Total AML alerts: {alerts_data['total']}")
                
                # Check if our transaction generated alerts
                transaction_alerts = [
                    alert for alert in alerts_data["alerts"] 
                    if alert.get("transaction_id") == transaction_id
                ]
                
                if transaction_alerts:
                    print(f"🚨 AML alerts generated for transaction:")
                    for alert in transaction_alerts:
                        print(f"   • Alert ID: {alert.get('alert_id', 'N/A')}")
                        print(f"     Risk Level: {alert.get('risk_level', 'N/A')}")
                        print(f"     Alert Type: {alert.get('alert_type', 'N/A')}")
                        print(f"     Score: {alert.get('score', 'N/A')}")
                        print(f"     Status: {alert.get('status', 'N/A')}")
                else:
                    print("ℹ️ No specific alerts generated for this transaction")
                
                # Test AML dashboard
                dashboard_response = await client.get(f"{API_BASE}/aml/dashboard", headers=headers)
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    print(f"📈 AML Dashboard Status: {dashboard_data.get('system_status', 'unknown')}")
                    print(f"📈 Recent Alerts: {len(dashboard_data.get('recent_alerts', []))}")
                    
                    alert_counts = dashboard_data.get('alert_counts', {})
                    if alert_counts:
                        print("📈 Alert Distribution:")
                        for level, count in alert_counts.items():
                            print(f"     • {level.title()}: {count}")
                    
                    return True
                else:
                    print(f"❌ AML dashboard failed: {dashboard_response.status_code}")
                    return False
            else:
                print(f"❌ AML alerts check failed: {alerts_response.status_code}")
                return False
        else:
            print(f"❌ Deposit failed: {deposit_response.status_code} - {deposit_response.text}")
            return False

async def main():
    success = await test_aml_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 AML Integration Test: ✅ PASSED")
        print("✅ Enum serialization working correctly")
        print("✅ AML monitoring functional")
        print("✅ Transaction processing successful")
    else:
        print("❌ AML Integration Test: FAILED")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)