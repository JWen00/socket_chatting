import json 

def loadClientBlockingData(filePath): 
    data = None 
    with open(filePath, "r") as f: 
        data = f.read() 
        if not data: 
            raise FileNotFoundError 
    return json.loads(data)
            

def setup(): 
    f = open("blockingData.txt", "w+") 
    data = { 
        "clientA" : [ 
            "clientB", "clientC", 
        ], 

        "clientB" : [
            "clientC", 
        ],

        "clientC" : [

        ], 
    }
    data = json.dumps(data) 
    f.write(data) 
    f.close  

setup() 
data = loadClientBlockingData("blockingData.txt") 
print(data) 

