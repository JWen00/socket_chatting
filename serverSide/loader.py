import os 
def loadCredentialsFile(filePath): 
    data = None
    with open(filePath, "r") as f: 
        data = f.read().splitlines()

    if not data: 
        raise FileNotFoundError 

    credentials_list = []
    for line in data:
        username, password = line.split(" ", 1)
        new_login = {}
        new_login["username"] = username
        new_login["password"] = password
        credentials_list.append(new_login) 

    return credentials_list

