import socket
import threading
import sys
import time
import os

# Server configuration
DEFAULT_PORT = 4000
BUFFER_SIZE = 1024

# ANSI color codes for better server logs (works in modern terminals)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Global dictionaries to track connected clients
clients = {}  # {socket: username}
usernames = {}  # {username: socket}
user_activity = {}  # {socket: last_activity_time}
lock = threading.Lock()

def log(message, color=Colors.RESET):
    """Print colored log messages"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{Colors.RESET}")

def broadcast_message(message, sender_socket=None, exclude_sockets=None):
    """Send message to all connected clients except sender and excluded sockets"""
    if exclude_sockets is None:
        exclude_sockets = []
    
    with lock:
        dead_sockets = []
        for client_socket in clients:
            if client_socket != sender_socket and client_socket not in exclude_sockets:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    dead_sockets.append(client_socket)
        
        # Remove dead connections
        for socket in dead_sockets:
            remove_client(socket)

def remove_client(client_socket):
    """Remove a client from all tracking dictionaries"""
    with lock:
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]
            del usernames[username]
            if client_socket in user_activity:
                del user_activity[client_socket]
            return username
    return None

def check_idle_clients():
    """Background thread to check for idle clients"""
    while True:
        time.sleep(10)  # Check every 10 seconds
        current_time = time.time()
        idle_sockets = []
        
        with lock:
            for socket, last_activity in user_activity.items():
                if current_time - last_activity > 60:  # 60 second timeout
                    idle_sockets.append(socket)
        
        for socket in idle_sockets:
            try:
                socket.send(b"INFO idle-timeout\n")
                username = remove_client(socket)
                if username:
                    log(f"User {username} disconnected (idle timeout)", Colors.YELLOW)
                    broadcast_message(f"INFO {username} disconnected\n")
                socket.close()
            except:
                pass

def handle_client(client_socket, client_address):
    """Handle individual client connection"""
    username = None
    
    try:
        # Set timeout for socket operations
        client_socket.settimeout(1.0)
        
        # Send welcome message
        client_socket.send(b"Welcome to AlgoKart Chat Server!\n")
        client_socket.send(b"Please login with: LOGIN <username>\n")
        
        while True:
            try:
                # Try to receive data
                try:
                    data = client_socket.recv(BUFFER_SIZE).decode('utf-8').strip()
                except socket.timeout:
                    continue
                
                if not data:
                    break
                
                # Update activity timestamp
                with lock:
                    user_activity[client_socket] = time.time()
                
                # Parse the command
                parts = data.split(' ', 1)
                command = parts[0].upper()
                
                # Handle LOGIN command
                if command == "LOGIN" and len(parts) > 1 and not username:
                    requested_username = parts[1].strip()
                    
                    # Validate username
                    if len(requested_username) < 3:
                        client_socket.send(b"ERR username-too-short (min 3 chars)\n")
                    elif len(requested_username) > 20:
                        client_socket.send(b"ERR username-too-long (max 20 chars)\n")
                    elif not requested_username.replace('_', '').isalnum():
                        client_socket.send(b"ERR username-invalid (alphanumeric and underscore only)\n")
                    else:
                        with lock:
                            if requested_username in usernames:
                                client_socket.send(b"ERR username-taken\n")
                            else:
                                username = requested_username
                                clients[client_socket] = username
                                usernames[username] = client_socket
                                user_activity[client_socket] = time.time()
                                client_socket.send(b"OK\n")
                                log(f"User '{username}' logged in from {client_address[0]}", Colors.GREEN)
                                
                                # Notify others
                                broadcast_message(f"INFO {username} joined the chat\n", client_socket)
                
                # Commands that require login
                elif not username:
                    client_socket.send(b"ERR not-logged-in (use LOGIN <username> first)\n")
                
                # Handle MSG command
                elif command == "MSG" and len(parts) > 1:
                    message = parts[1]
                    broadcast_msg = f"MSG {username} {message}\n"
                    broadcast_message(broadcast_msg, client_socket)
                    log(f"{username}: {message}", Colors.BLUE)
                
                # Handle WHO command
                elif command == "WHO":
                    with lock:
                        user_list = list(usernames.keys())
                    
                    client_socket.send(f"INFO {len(user_list)} users online\n".encode('utf-8'))
                    for user in sorted(user_list):
                        status = " (you)" if user == username else ""
                        client_socket.send(f"USER {user}{status}\n".encode('utf-8'))
                
                # Handle DM command
                elif command == "DM" and len(parts) > 1:
                    dm_parts = parts[1].split(' ', 1)
                    if len(dm_parts) >= 2:
                        target_user = dm_parts[0]
                        dm_message = dm_parts[1]
                        
                        if target_user == username:
                            client_socket.send(b"ERR cannot-dm-self\n")
                        else:
                            with lock:
                                if target_user in usernames:
                                    target_socket = usernames[target_user]
                                    target_socket.send(f"DM {username} {dm_message}\n".encode('utf-8'))
                                    client_socket.send(b"OK\n")
                                    log(f"DM: {username} -> {target_user}: {dm_message}", Colors.YELLOW)
                                else:
                                    client_socket.send(b"ERR user-not-found\n")
                    else:
                        client_socket.send(b"ERR invalid-format (use DM <username> <message>)\n")
                
                # Handle PING command
                elif command == "PING":
                    client_socket.send(b"PONG\n")
                
                # Handle HELP command
                elif command == "HELP":
                    help_text = """Available commands:
LOGIN <username> - Login with a username
MSG <message> - Send message to all users  
WHO - List online users
DM <username> <message> - Send private message
PING - Check connection
HELP - Show this help
"""
                    client_socket.send(help_text.encode('utf-8'))
                
                else:
                    client_socket.send(b"ERR unknown-command (type HELP for commands)\n")
                    
            except UnicodeDecodeError:
                client_socket.send(b"ERR invalid-encoding\n")
            except Exception as e:
                log(f"Error in client loop: {e}", Colors.RED)
                break
                
    except Exception as e:
        log(f"Error handling client {client_address}: {e}", Colors.RED)
    finally:
        # Cleanup
        if username:
            removed_user = remove_client(client_socket)
            if removed_user:
                disconnect_msg = f"INFO {removed_user} disconnected\n"
                broadcast_message(disconnect_msg)
                log(f"User '{removed_user}' disconnected", Colors.YELLOW)
        
        client_socket.close()

def main():
    # Clear screen for clean start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # ASCII Art Banner
    print(Colors.HEADER + """
    ╔═══════════════════════════════════════╗
    ║     AlgoKart Chat Server v1.0         ║
    ╚═══════════════════════════════════════╝
    """ + Colors.RESET)
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('', port))
        server_socket.listen(10)
        
        log(f"Server started on port {port}", Colors.GREEN)
        log("Waiting for connections...", Colors.BLUE)
        log("Press Ctrl+C to stop the server\n", Colors.YELLOW)
        
        # Start idle client checker thread
        idle_checker = threading.Thread(target=check_idle_clients)
        idle_checker.daemon = True
        idle_checker.start()
        
        # Main server loop
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                log(f"New connection from {client_address[0]}:{client_address[1]}", Colors.GREEN)
                
                # Create a thread to handle this client
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                log("\nShutting down server...", Colors.YELLOW)
                break
                
    except Exception as e:
        log(f"Error starting server: {e}", Colors.RED)
    finally:
        # Clean shutdown
        with lock:
            for client_socket in list(clients.keys()):
                try:
                    client_socket.send(b"INFO server-shutdown\n")
                    client_socket.close()
                except:
                    pass
        
        server_socket.close()
        log("Server stopped", Colors.RED)

if __name__ == "__main__":
    main()
