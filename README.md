# AlgoKart Chat Server

High-performance TCP chat server built with Python's standard library (`socket`, `threading`). It supports multiple concurrent users, real-time messaging, and a simple but robust text protocol.


## Demo Video

[Watch the demo video](https://drive.google.com/file/d/1guU1h10-7POLeoBcrQGLaZdB-kGhzzrc/view?usp=sharing)


## Github Repository
[Github repo](https://github.com/MrKunalSharma/algokart-chat-server.git)



## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Connecting to the Server](#connecting-to-the-server)
- [Protocol](#protocol)
- [Example Sessions](#example-sessions)
- [Architecture](#architecture)
- [Error Handling](#error-handling)
- [Author](#author)


## Features

**Core**
- Multi-client support (10+ concurrent users)
- Username-based login with validation
- Real-time message broadcasting
- Graceful disconnect notifications

**Bonus**
- List active users (`WHO` command)
- Private messaging (`DM <user> <message>`)
- 60-second idle timeout
- `PING`/`PONG` heartbeat
- Thread-safe operations


## Requirements

- Python 3.6+
- No external dependencies (standard library only)


## Quick Start

Run the server (default port 4000):

```bash
python chat_server.py
```

Run the server on a custom port:

```bash
python chat_server.py 5000
```


## Connecting to the Server

Using the provided test client:

```bash
python test_client.py
```

Using telnet:

```bash
telnet localhost 4000
```

Using netcat (nc):

```bash
nc localhost 4000
```


## Protocol

| Command | Description | Example |
|---|---|---|
| `LOGIN <username>` | Authenticate with a unique username | `LOGIN Alice` |
| `MSG <message>` | Broadcast message to all users | `MSG Hello everyone!` |
| `WHO` | List all active users | `WHO` |
| `DM <username> <message>` | Send private message to a user | `DM Bob Hey there!` |
| `PING` | Heartbeat check (responds with PONG) | `PING` |


## Example Sessions

Client 1 (Alice):

```text
> LOGIN Alice
< OK
> MSG Hi everyone!
> WHO
< USER Alice
< USER Bob
< MSG Bob Hello Alice!
> DM Bob Thanks for joining!
< OK
```

Client 2 (Bob):

```text
> LOGIN Bob
< OK
> MSG Hello Alice!
< MSG Alice Hi everyone!
< DM Alice Thanks for joining!
> quit
```

Others see:

```text
< INFO Bob disconnected
```


## Architecture

- Multi-threaded: each client connection is handled in a dedicated thread
- Thread-safe: shared state guarded by locks
- Efficient: socket timeouts to detect idle connections
- Scalable: supports multiple simultaneous connections


## Error Handling

- Username validation (prevents duplicates/invalid names)
- Graceful disconnection and cleanup
- Idle timeout for inactive clients
- Invalid command handling with informative responses
- UTF-8 decoding and validation


## Author

Created for AlgoKart Backend Internship Assignment.