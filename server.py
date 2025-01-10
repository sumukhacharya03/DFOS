import socket
import threading
import os
import time
import signal
import sys
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor

# Configure performance logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('server_performance.log'),  # Writes to file
        logging.StreamHandler()  # Displays in terminal
    ]
)

# Global performance tracking variables
class PerformanceTracker:
    def __init__(self):
        self.active_connections = 0
        self.total_connections = 0
        self.file_transfers = 0
        self.transfer_lock = threading.Lock()

    def increment_connections(self):
        with self.transfer_lock:
            self.active_connections += 1
            self.total_connections += 1

    def decrement_connections(self):
        with self.transfer_lock:
            self.active_connections -= 1

    def log_file_transfer(self):
        with self.transfer_lock:
            self.file_transfers += 1

performance_tracker = PerformanceTracker()

def load_credentials(filename='id_passwd.txt'):
    credentials = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and ':' in line:
                user, pwd = line.split(':', 1)
                credentials[user] = pwd
    return credentials

def authenticate(client_socket):
    count=1
    while (count<=3):    
        client_socket.sendall(b"Username: ")
        username = client_socket.recv(1024).decode().strip()
        client_socket.sendall(b"Password: ")
        password = client_socket.recv(1024).decode().strip()
        credentials = load_credentials()
        if username in credentials and credentials[username] == password:
            client_socket.sendall(b"Authentication successful.")
            print("Authentication Successful")
            logging.info(f"Authentication Successful for user {username}")
            time.sleep(0.1)
            return username
        else:
            client_socket.sendall(b"Authentication failed.")
            time.sleep(0.1)
            print("Authentication failed")
            logging.warning(f"Authentication failed for user {username}")
            count+=1
            
    logging.error(f"Multiple failed authentication attempts for user {username}")
    return None

def handle_file_upload(client_socket, user):
    start_time = time.time()
    try:
        client_socket.sendall(b"Ready to receive the filename.")
        filename = client_socket.recv(1024).decode().strip()
        
        if filename == "CANCEL_UPLOAD":
            print(f"Upload cancelled by user {user}")
            logging.info(f"Upload cancelled by user {user}")
            return
            
        if not filename:
            client_socket.sendall(b"Invalid filename.")
            return

        user_dir = os.path.join("server_storage", user)
        os.makedirs(user_dir, exist_ok=True)

        filepath = os.path.join(user_dir, filename)
        client_socket.sendall(b"Ready to receive file data.")
        time.sleep(0.1)

        with open(filepath, 'wb') as file:
            total_bytes = 0
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    print(f"Client {user} disconnected unexpectedly.")
                    logging.warning(f"Client {user} disconnected unexpectedly.")
                    return
                if chunk == b'END_OF_FILE':
                    break
                if chunk == b'UPLOAD_ERROR':
                    print(f"Upload error reported by client {user}")
                    logging.error(f"Upload error reported by client {user}")
                    return
                file.write(chunk)
                total_bytes += len(chunk)
                client_socket.sendall(b"Chunk received.")

        end_time = time.time()
        performance_tracker.log_file_transfer()
        logging.info(f"File upload completed: {filename}, User: {user}, Size: {total_bytes} bytes, Duration: {end_time - start_time:.2f}s")
        client_socket.sendall(b"File upload completed successfully.")
        print(f"File {filename} uploaded successfully for user {user}")
        
    except BrokenPipeError:
        print(f"Broken pipe error with client {user}.")
        logging.error(f"Broken pipe error with client {user}.")
    except Exception as e:
        print(f"Error while handling file upload for user {user}: {e}")
        logging.error(f"File upload error for user {user}: {e}")
        try:
            client_socket.sendall(b"Error: Failed to receive file data.")
        except:
            pass

def handle_file_download(client_socket, user):
    try:
        request = client_socket.recv(1024).decode().strip()
        
        if request.startswith("PREVIEW "):
            preview_mode = True
            filename = request[8:]
        else:
            preview_mode = False
            filename = request

        user_dir = os.path.join("server_storage", user)
        filepath = os.path.join(user_dir, filename)
        
        if not os.path.exists(filepath):
            client_socket.sendall(b"FILE_NOT_FOUND")
            time.sleep(0.1)
            logging.warning(f"File not found: {filename} for user {user}")
            return

        logging.info(f"Handling {'preview' if preview_mode else 'download'} request for {filename} by user {user}")

        if preview_mode:
            client_socket.sendall(b"PREVIEW_MODE")
            time.sleep(0.1)
            
            with open(filepath, 'rb') as file:
                preview_data = file.read(1024)
                client_socket.sendall(preview_data)
            
            time.sleep(0.1)
            client_socket.sendall(b"END_OF_PREVIEW")
            
        else:
            client_socket.sendall(b"FILE_FOUND")
            time.sleep(0.1)
            
            with open(filepath, 'rb') as file:
                while chunk := file.read(1024):
                    client_socket.sendall(chunk)
                    time.sleep(0.01)
                
            time.sleep(0.1)
            client_socket.sendall(b"END_OF_FILE")
            
        print(f"Successfully handled {'preview' if preview_mode else 'download'} request for {filename} by user {user}")
        logging.info(f"Successfully completed {'preview' if preview_mode else 'download'} for {filename} by user {user}")
        
    except Exception as e:
        print(f"Error while handling file {'preview' if preview_mode else 'download'} for user {user}: {e}")
        logging.error(f"File {'preview' if preview_mode else 'download'} error for user {user}: {e}")
        try:
            client_socket.sendall(b"ERROR")
        except:
            pass

def handle_file_deletion(client_socket, user):
    try:
        client_socket.sendall(b"Enter the filename to delete: ")
        filename = client_socket.recv(1024).decode().strip()

        user_dir = os.path.join("server_storage", user)
        filepath = os.path.join(user_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            client_socket.sendall(b"FILE_DELETED")
            print(f"File {filename} deleted for user {user}")
            logging.info(f"File {filename} deleted for user {user}")
            time.sleep(0.1)
        else:
            client_socket.sendall(b"FILE_NOT_FOUND")
            logging.warning(f"File not found for deletion: {filename} for user {user}")
    except BrokenPipeError:
        print(f"Broken pipe error with client {user}.")
        logging.error(f"Broken pipe error with client {user}.")
    except Exception as e:
        print(f"Error while handling file deletion for user {user}: {e}")
        logging.error(f"File deletion error for user {user}: {e}")
        try:
            client_socket.sendall(b"Error: Failed to delete file.")
        except:
            pass

def handle_client(client_socket, client_address):
    performance_tracker.increment_connections()
    print(f"Connection from {client_address} established.")
    logging.info(f"New connection from {client_address}")
    logging.info(f"Active Connections: {performance_tracker.active_connections}")
    try:
        user = authenticate(client_socket)
        if not user:
            client_socket.close()
            return

        print(f"User '{user}' authenticated successfully from {client_address}")

        while True:
            try:
                client_socket.sendall(b"Enter command (upload/download/delete/exit): ")
                command = client_socket.recv(1024).decode().strip()

                if command == 'upload':
                    print(f"User {user} requested file upload.")
                    handle_file_upload(client_socket, user)
                elif command == 'download':
                    print(f"User {user} requested file download.")
                    handle_file_download(client_socket, user)
                elif command == 'delete':
                    print(f"User {user} requested file deletion.")
                    handle_file_deletion(client_socket, user)
                elif command == 'exit':
                    print(f"User {user} exited.")
                    logging.info(f"User {user} exited.")
                    break
                else:
                    client_socket.sendall(b"Invalid command.")
            except BrokenPipeError:
                print(f"Connection lost with client {client_address}")
                logging.error(f"Connection lost with client {client_address}")
                break
            except Exception as e:
                print(f"Error handling command for {client_address}: {e}")
                logging.error(f"Error handling command for {client_address}: {e}")
                break

    except Exception as e:
        print(f"Error with client {client_address}: {e}")
        logging.error(f"Error with client {client_address}: {e}")
    finally:
        print(f"Connection from {client_address} closed.")
        performance_tracker.decrement_connections()
        logging.info(f"Connection from {client_address} closed.")
        try:
            client_socket.close()
        except:
            pass

def signal_handler(signum, frame):
    logging.info("\nServer shutdown initiated.")
    logging.info(f"Total Connections: {performance_tracker.total_connections}")
    logging.info(f"Active Connections: {performance_tracker.active_connections}")
    logging.info(f"File Transfers: {performance_tracker.file_transfers}")
    
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    logging.info(f"Final System Resources - CPU: {cpu_usage}%, Memory: {memory_usage}%")
    
    print("\nServer is shutting down gracefully...")
    sys.exit(0)

def main():
    logging.info("Server started. Initializing performance tracking.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 5000))
    server_socket.listen(5)
    print("Server is listening on port 5000...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                executor.submit(handle_client, client_socket, client_address)
        except KeyboardInterrupt:
            print("\nServer is shutting down.")
        finally:
            server_socket.close()

if __name__ == "__main__":
    main()
