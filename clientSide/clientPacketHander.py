import json

def constructReq(command, data=None): 
    req = {} 
    req["command"] = command 
    req["data"] = data
    req = json.dumps(req) 
    req = req.encode() 
    return req 

def decodeResponse(response): 
    response = response.decode() 
    response = json.loads(response) 
    status = response.get("status") 
    data = response.get("data") 
    return status, data 
