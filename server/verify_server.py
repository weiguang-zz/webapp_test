import asyncio
import websockets
import json
import sys

async def test_advanced_features():
    uri = "ws://localhost:8090"
    
    # 1. Create Room (Chinese ID)
    print("Test 1: Create Room with Chinese ID")
    async with websockets.connect(uri) as ws1:
        await ws1.send(json.dumps({
            "type": "join",
            "payload": {
                "roomId": "测试房间",
                "password": "123",
                "create": True,
                "userInfo": {"nickName": "User1"}
            }
        }))
        res = await ws1.recv()
        print(f"User1 received: {res}")
        if "error" not in res:
            print("PASS: Created Chinese room")
        else:
            print("FAIL: Failed to create Chinese room")

    # 2. Create Existing Room (Should Fail)
    print("\nTest 2: Create Existing Room")
    async with websockets.connect(uri) as ws2:
        await ws2.send(json.dumps({
            "type": "join",
            "payload": {
                "roomId": "测试房间",
                "create": True,
                "userInfo": {"nickName": "User2"}
            }
        }))
        res = await ws2.recv()
        print(f"User2 received: {res}")
        if "error" in res and "房间已存在" in res:
            print("PASS: Correctly rejected creating existing room")
        else:
            print("FAIL: Did not reject existing room creation")

    # 3. Join Non-Existing Room (Should Fail)
    print("\nTest 3: Join Non-Existing Room")
    async with websockets.connect(uri) as ws3:
        await ws3.send(json.dumps({
            "type": "join",
            "payload": {
                "roomId": "不存在的房间",
                "create": False,
                "userInfo": {"nickName": "User3"}
            }
        }))
        res = await ws3.recv()
        print(f"User3 received: {res}")
        if "error" in res and "房间不存在" in res:
            print("PASS: Correctly rejected joining non-existing room")
        else:
            print("FAIL: Did not reject non-existing room join")

    # 4. Join with Password
    print("\nTest 4: Join with Password")
    async with websockets.connect(uri) as ws4:
        await ws4.send(json.dumps({
            "type": "join",
            "payload": {
                "roomId": "测试房间",
                "password": "123",
                "create": False,
                "userInfo": {"nickName": "User4"}
            }
        }))
        res = await ws4.recv()
        print(f"User4 received: {res}")
        if "error" not in res:
            print("PASS: Joined with correct password")
        else:
            print("FAIL: Failed to join with correct password")

    # 5. Test Persistence Resurrection (Simulated)
    # Note: We can't easily restart server here, but we can check if joining a "known" persisted room works 
    # if we assume the server was restarted before this script ran (which we will do manually).
    # Or we can rely on the fact that "测试房间" was created in Test 1.
    # If we run this script TWICE, the second time Test 1 should FAIL (Room exists), 
    # and Test 4 should SUCCEED (Room exists).
    
    print("\nTest 5: Create Existing Persisted Room (Should Fail)")
    async with websockets.connect(uri) as ws5:
        await ws5.send(json.dumps({
            "type": "join",
            "payload": {
                "roomId": "测试房间",
                "create": True,
                "userInfo": {"nickName": "User5"}
            }
        }))
        res = await ws5.recv()
        print(f"User5 received: {res}")
        if "error" in res and "房间已存在" in res:
            print("PASS: Correctly rejected creating existing persisted room")
        else:
            print("FAIL: Did not reject existing persisted room creation")

if __name__ == "__main__":
    asyncio.run(test_advanced_features())
