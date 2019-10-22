import json 

def constructResponse(status, data=None): 
    response = {} 
    response["status"] = status 
    response["data"] = data
    response = json.dumps(response) 
    response = response.encode() 
    return response 

def decodeReq(req):
    req = req.decode() 
    req = json.loads(req) 
    command = req.get("command") 
    data = req.get("data") 
    return command, data 
