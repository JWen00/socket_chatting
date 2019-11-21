# COMP3331 Assignment Report (z5207930)

## Program Design 

### Server side 
Server side composes of the file `server.py`, `docs`, and `src`.

* `server.py` contains the starter code for the server implementation
* `docs` contains `credentials.txt`
* `src` contains all supporting code including `server.py`, `clientManager.py` and `session.py`. 

NOTE: `server.py` is a class which manager server client interactions while `clientManager.py` manages all the data relating to the clients. 

### Client side 
Client side is a little simpler, there is a `client.py` as required, and a `clientClass.py`. 

Because we had to name the client with a file called `client.py`, there is an awkward naming going on. (I would much rather have `client.py` be called `runClient.py` or something along those lines.)


## Application Layer Message Format 
Both client and server side have a two functions called:

* constructResponse(command/status, data)
* decodeResponse(response) 

My assignemt uses JSON to pass messages between each other: 

```
messageToSend = { 
    "command" : "someCommand", 
    "data" : ["args", "made", "into", "a", "list"]
}
```

This makes it quick and easy to digest messages and gather required arguments as well as check when there not enough arguments by checking the size of "data".

## How the system works 

Server starts up, waiting for connections and then continously listens for new connections and any data received from made connections. 

The server processes the data appropriately, keeping track of all client activity using clientManager.

Client starts up keeps prompting the client to log in until either successful or blocked by the server, causing the program to terminate. 

Client sends all commands to be processed by the server except for `private` and `stopprivate`. 

Client also simultaneously has a socket to listen for any incoming connections attempting to start a private chat and keeps listening for information from the server, new peer connections or information from peer connections. 

## Design Tradeoffs 

At first I only wanted to store information about the clients who were active - but this conflicted with my code a little bit so I ended up creating a profile for each login credential in the `__init__()`

It was also a tough desision to use classes for the client and server files as I had alot of global data to store. I felt that because it was a class, it also had its limitations. 

## Improvements and extensions 

If I had more time I would have implemented persistant blocking and a proper history for the chats and login done by clients. 

I would also want to make clientside more secure just with lots of things I didn't quite have time to do - like hashing passwords, more secure way of storing client data and probably not using a dictionary to store EVERYTHING. 

## Things that don't quite work.

* timeout doesnt work. 
* didn't do extension 