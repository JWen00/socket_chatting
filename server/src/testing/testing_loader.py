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

# Testing above code
# username = "123"
# password = "456" 
# login_credentials = loadCredentialsFile("credentials.txt") 
# for credential in login_credentials: 
#     if credential["username"] == username and credential["password"] == password: 
#         print("Correct!") 
#     else: 
#         print("Nope D:") 