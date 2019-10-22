# sends a message to a user through the server 
def message(user, destination, message): 

    # Check validity
    if user blocked by destination: 
        send message to user("You cannot message " + destination)  

    elif destination does not exist: 
        send message to user("Invalid user: " + destination) 

    elif destination == user: 
        send message to user("Cannot escape lonliness..")
    if  user is online: 
        deliver
    else: 
        store in server 

# Send message to all online users except user and people who have blocked A
def broadcast(user, message): 
    should I have the block cehcking done in the serer or on the client side? 

def whoelse(): 
    get this done through the server.. 
    display the response 

def whoelsesince(user, time): 
    # Parse and check time 
    get this done through the server 
    display the response 

def block(user, destination): 
    add to list of blocked people 
    send information to server 

def unblock(user, destination):
    delete from list of blocked people 
    send information to server

def logout(user): 
    # user doesn't have to have a log of it's login data right? 
    return constructResponse("logout", user.name)



