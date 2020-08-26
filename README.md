# Socket Chatting

This is a networks assignment to write a terminal messenger.

Rather than using higher level modules like `socketio`, it uses a low-level networking interface - `socket`.

## Setup

Open two teminals

```bash
python3 client.py <serverPort> <portNumber>
```

```bash
python3 server.py <server_port> <block_duration> <timeout>
```

## Server side

Server side composes of the file `server.py`, `docs`, and `src`.

- `server.py` contains the starter code for the server implementation
- `docs` contains `credentials.txt`
- `src` contains all supporting code including `server.py`, `clientManager.py` and `session.py`.

NOTE: `server.py` is a class which manager server client interactions while `clientManager.py` manages all the data relating to the clients.

## Client side

Client side is a little simpler, there is a `client.py` as required, and a `clientClass.py`.

Because we had to name the client with a file called `client.py`, there is an awkward naming going on. (I would much rather have `client.py` be called `runClient.py` or something along those lines.)

## Application Layer Message Format

Both client and server side have a two functions called:

- constructResponse(command/status, data)
- decodeResponse(response)

These functions format the data using JSON.

```json
{
  "command": "someCommand",
  "data": ["args", "made", "into", "a", "list"]
}
```

Commands include:

- login
- broadcast
- whoelse
- whoelsesince
- block
- unblock
- startprivate
- message

## How it works

1. Server starts up and waits for connections and continously listens for new connections and any data received from made connections

2. server processes the data appropriately, keeping track of all client activity using clientManager.

3. Client starts up, and keeps prompting the user to log in until either successful or blocked by the server, causing the program to terminate.

4. Client sends all commands to be processed by the server except for `private` and `stopprivate`.

5. Client also simultaneously has a socket to listen for any incoming connections attempting to start a private chat and keeps listening for information from the server, new peer connections or information from peer connections.

## Design Tradeoffs

At first I only wanted to store information about the clients who were active - but this conflicted with my code so I ended up creating a profile for each login credential in the `__init__()`

It was also a tough desision to use classes for the client and server files as I had alot of global data to store. I felt that because it was a class, it also had its limitations.

## Improvements and extensions

- persistant blocking and a proper history for the chats and login done by clients.
- make clientside more secure - hashing passwords
- make a secure way of storing client data and probably not using a dictionary to store EVERYTHING.
- timeout doesnt work
