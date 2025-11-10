import socket
import threading
import time
import msvcrt
import sys

class ChatClient:
    def __init__(self):
        self.sock = None
        self.running = True
        
    def receive_messages(self):
        """Background thread to receive messages"""
        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8').strip()
                if data:
                    print(f"\n<< {data}")
                    print(">> ", end='', flush=True)
                else:
                    print("\nServer disconnected")
                    self.running = False
                    break
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"\nConnection error: {e}")
                break
    
    def connect(self):
        """Connect to the server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1.0)
        
        try:
            self.sock.connect(('localhost', 4000))
            print("Connected to AlgoKart Chat Server!")
            print("=" * 50)
            print("Commands:")
            print("  LOGIN <username>  - Login with your username")
            print("  MSG <message>     - Send message to all users")
            print("  WHO              - List online users")
            print("  DM <user> <msg>  - Send private message")
            print("  PING             - Test connection")
            print("  HELP             - Show server commands")
            print("  quit             - Exit")
            print("=" * 50)
            
            # Start receiver thread
            receiver = threading.Thread(target=self.receive_messages)
            receiver.daemon = True
            receiver.start()
            
            return True
        except Exception as e:
            print(f"Could not connect to server: {e}")
            return False
    
    def run(self):
        """Main client loop"""
        if not self.connect():
            return
        
        time.sleep(0.5)  # Let welcome messages arrive
        
        try:
            while self.running:
                print(">> ", end='', flush=True)
                command = input()
                
                if command.lower() == 'quit':
                    break
                
                if command.strip():
                    self.sock.send(f"{command}\n".encode('utf-8'))
                    
        except KeyboardInterrupt:
            print("\n\nDisconnecting...")
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            self.running = False
            if self.sock:
                self.sock.close()
            print("Goodbye!")

if __name__ == "__main__":
    client = ChatClient()
    client.run()

