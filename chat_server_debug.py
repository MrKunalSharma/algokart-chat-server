import socket
import threading
import sys
import time

DEFAULT_PORT = 4000
BUFFER_SIZE = 1024

clients = {}
usernames = {}
lock = threading.Lock()

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def broadcast_message(message, sender_socket=None):
    """Send message to all connected clients except sender"""
    with lock:
        for client_socket in clients:
            if client_socket != sender_socket:
                try:
                    log(f"Broadcasting to {clients[client_socket]}: {message.strip()}")
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    log(f"Failed to send to {clients[client_socket]}: {e}")

def handle_client(client_socket, client_address):
    username = None
    
    try:
        # Send welcome
        client_socket.send(b"Welcome to AlgoKart Chat Server!\n")
        client_socket.send(b"Please login with: LOGIN <username>\n")
        
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE).decode('utf-8').strip()
                
                if not data:
                    break
                
                log(f"Received from {client_address}: '{data}'")
                parts = data.split(' ', 1)
                command = parts[0].upper()
                
                # LOGIN command
                if command == "LOGIN" and len(parts) > 1 and not username:
                    requested_username = parts[1].strip()
                    
                    with lock:
                        if requested_username in usernames:
                            response = "ERR username-taken\n"
                            log(f"Login failed for {requested_username} - username taken")
                        else:
                            username = requested_username
                            clients[client_socket] = username
                            usernames[username] = client_socket
                            response = "OK\n"
                            log(f"Login successful for {username}")
                    
                    client_socket.send(response.encode('utf-8'))
                    
                    if username:
                        # Notify others
                        broadcast_message(f"INFO {username} joined the chat\n", client_socket)
                
                elif not username:
                    response = "ERR not-logged-in\n"
                    client_socket.send(response.encode('utf-8'))
                    log(f"Command rejected - user not logged in")
                
                # MSG command
                elif command == "MSG" and len(parts) > 1:
                    message = parts[1]
                    broadcast_msg = f"MSG {username} {message}\n"
                    broadcast_message(broadcast_msg, client_socket)
                    log(f"Message from {username}: {message}")
                
                # WHO command
                elif command == "WHO":
                    with lock:
                        response = f"INFO {len(usernames)} users online\n"
                        client_socket.send(response.encode('utf-8'))
                        for user in usernames:
                            response = f"USER {user}\n"
                            client_socket.send(response.encode('utf-8'))
                            log(f"Sent user list to {username}: {user}")
                
                # PING command
                elif command == "PING":
                    client_socket.send(b"PONG\n")
                    log(f"PONG sent to {username}")
                
                # HELP command
                elif command == "HELP":
                    help_text = """Available commands:
LOGIN <username> - Login with username
MSG <message> - Send message to all
WHO - List online users
PING - Check connection
HELP - Show this help
"""
                    client_socket.send(help_text.encode('utf-8'))
                    log(f"HELP sent to {username}")
                
                # DM command
                elif command == "DM" and len(parts) > 1:
                    dm_parts = parts[1].split(' ', 1)
                    if len(dm_parts) >= 2:
                        target_user = dm_parts[0]
                        dm_message = dm_parts[1]
                        
                        with lock:
                            if target_user in usernames:
                                target_socket = usernames[target_user]
                                dm_msg = f"DM {username} {dm_message}\n"
                                target_socket.send(dm_msg.encode('utf-8'))
                                client_socket.send(b"OK\n")
                                log(f"DM from {username} to {target_user}: {dm_message}")
                            else:
                                client_socket.send(b"ERR user-not-found\n")
                                log(f"DM failed - {target_user} not found")
                    else:
                        client_socket.send(b"ERR invalid-format\n")
                
                else:
                    client_socket.send(b"ERR unknown-command\n")
                    log(f"Unknown command from {username}: {command}")
                    
            except Exception as e:
                log(f"Error handling {username or client_address}: {e}")
                break
                
    except Exception as e:
        log(f"Fatal error with {username or client_address}: {e}")
    finally:
        # Cleanup
        if username:
            with lock:
                if client_socket in clients:
                    del clients[client_socket]
                    del usernames[username]
            
            broadcast_message(f"INFO {username} disconnected\n")
            log(f"{username} disconnected")
        
        client_socket.close()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('', port))
        server_socket.listen(10)
        log(f"Chat server started on port {port}")
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                log(f"New connection from {client_address}")
                
                thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                thread.daemon = True
                thread.start()
                
            except KeyboardInterrupt:
                break
                
    finally:
        server_socket.close()
        log("Server stopped")

if __name__ == "__main__":
    main()
