import socket
import os
import time
import signal
import sys

#Captures (Ctrl+C) signals and gracefully terminates the client program to avoid abrupt exits.
def handle_sigint(signum, frame):
    print("\nReceived interrupt signal. Exiting gracefully...")
    sys.exit(0)

#Displays the contents of a directory. The files and folders are separated with numbering and navigation options for easy browsing.
def list_directory(path="."):
    """List contents of a directory with numbering."""
    try:
        # Get directory contents
        contents = sorted(os.listdir(path))
        # Separate directories and files
        directories = [d for d in contents if os.path.isdir(os.path.join(path, d))]
        files = [f for f in contents if os.path.isfile(os.path.join(path, f))]
        
        print("\nCurrent directory:", os.path.abspath(path))
        print("\nDirectories:")
        for i, dirname in enumerate(directories, 1):
            print(f"{i}. [{dirname}]")
        
        print("\nFiles:")
        for i, filename in enumerate(files, len(directories) + 1):
            print(f"{i}. {filename}")
        
        print("\nNavigation options:")
        print("0. Select current file")
        print(".. Go to parent directory")
        print("/ Go to root directory")
        print("~ Go to home directory")
        print("exit Exit file browser")
        
        return directories, files
    except Exception as e:
        print(f"Error listing directory: {e}")
        return [], []

#Allows users to explore directories by picking a file for uploading, downloading, or deleting, with options to navigate folders or enter a file path directly.
def browse_for_file():
    """Interactive file browser."""
    current_path = os.getcwd()
    
    while True:
        directories, files = list_directory(current_path)
        
        choice = input("\nEnter selection (number/path/navigation option): ").strip()
        
        # Handle exit option
        if choice.lower() == "exit":
            return None
            
        # Handle navigation options
        if choice == "..":
            current_path = os.path.dirname(current_path)
            continue
        elif choice == "/":
            current_path = "/"
            continue
        elif choice == "~":
            current_path = os.path.expanduser("~")
            continue
        elif choice == "0":
            return current_path
        
        # Handle numeric selection
        try:
            idx = int(choice)
            if 1 <= idx <= len(directories):
                # Selected a directory
                current_path = os.path.join(current_path, directories[idx-1])
            elif len(directories) < idx <= len(directories) + len(files):
                # Selected a file
                return os.path.join(current_path, files[idx-len(directories)-1])
            else:
                print("Invalid selection number.")
        except ValueError:
            # Handle direct path input
            if os.path.exists(choice):
                if os.path.isdir(choice):
                    current_path = choice
                else:
                    return choice
            else:
                print("Invalid path or selection.")

#Allows the users to upload a file to the server by navigating to the desired file, ensuring it exists and is accessible, and then sending it over in chunks.
def upload_file(client_socket):
    try:
        initial_response = client_socket.recv(1024).decode()
        print(initial_response)
        
        print("\nFile Browser - Navigate to your file:")
        print("Current working directory:", os.getcwd())
        print("Type '..' to go up one directory")
        print("Type '/' to go to root directory")
        print("Type '~' to go to home directory")
        print("Type 'exit' to return to main menu")
        print("Or enter the full path to your file")
        
        selected_path = browse_for_file()
        if selected_path is None:  # User chose to exit
            print("Returning to main menu...")
            client_socket.sendall(b"CANCEL_UPLOAD")
            return False
            
        if os.path.isdir(selected_path):
            print("Please select a file, not a directory.")
            client_socket.sendall(b"CANCEL_UPLOAD")
            return False
            
        abs_path = os.path.abspath(selected_path)
        print(f"\nSelected file: {abs_path}")
        
        if not os.path.exists(abs_path):
            print(f"File does not exist at path: {abs_path}")
            client_socket.sendall(b"CANCEL_UPLOAD")
            return False
        
        if not os.access(abs_path, os.R_OK):
            print(f"File exists but is not readable: {abs_path}")
            client_socket.sendall(b"CANCEL_UPLOAD")
            return False
            
        # Send just the basename, not the full path
        client_socket.sendall(os.path.basename(abs_path).encode())
        response = client_socket.recv(1024).decode()
        print(response)
        
        if response != "Ready to receive file data.":
            return False
        
        try:
            file_size = os.path.getsize(abs_path)
            print(f"Starting upload of {file_size} bytes...")
            
            with open(abs_path, 'rb') as file:
                bytes_sent = 0
                while chunk := file.read(1024):
                    client_socket.sendall(chunk)
                    ack = client_socket.recv(1024).decode()
                    bytes_sent += len(chunk)
                    print(f"Progress: {bytes_sent}/{file_size} bytes ({(bytes_sent/file_size)*100:.1f}%)")
                    if ack != "Chunk received.":
                        print("Error in transmission, retrying...")
                        client_socket.sendall(chunk)
        except Exception as e:
            print(f"Error during file upload: {e}")
            client_socket.sendall(b'UPLOAD_ERROR')
            return False
        
        client_socket.sendall(b'END_OF_FILE')
        final_response = client_socket.recv(1024).decode()
        print(final_response)
        return True
        
    except Exception as e:
        print(f"Error in upload process: {e}")
        return False

#Allows users to download a file from the server and enables them to preview the first few bytes of the file if requested.
def download_file(client_socket):
    try:
        filename = input("Enter the filename to download or type 'PREVIEW <filename>' for a byte preview: ").strip()
        
        # Send the request to server
        client_socket.sendall(filename.encode())
        
        # Get initial response from server
        response = client_socket.recv(1024).decode()
        
        if response == "FILE_NOT_FOUND":
            print("Error: File not found on server.")
            return False
            
        elif response == "PREVIEW_MODE":
            print("\n--- Preview of the file's first 1024 bytes ---")
            preview_data = b""
            
            while True:
                chunk = client_socket.recv(1024)
                if chunk.endswith(b"END_OF_PREVIEW"):
                    preview_data += chunk[:-14]  # Remove END_OF_PREVIEW marker
                    break
                preview_data += chunk
            
            try:
                print(preview_data.decode('utf-8'))
            except UnicodeDecodeError:
                print("[Binary data preview]")
            print("\n--- End of Preview ---")
            return True
            
        elif response == "FILE_FOUND":
            print(f"Downloading file: {filename}")
            save_name = filename.split('/')[-1]  # Get just the filename part
            
            with open(save_name, 'wb') as file:
                while True:
                    chunk = client_socket.recv(1024)
                    if chunk.endswith(b"END_OF_FILE"):
                        file.write(chunk[:-11])  # Remove END_OF_FILE marker
                        break
                    file.write(chunk)
            
            print(f"File {save_name} downloaded successfully.")
            return True
            
        elif response == "ERROR":
            print("Server encountered an error while processing the request.")
            return False
            
        else:
            print(f"Unexpected server response: {response}")
            return False
            
    except Exception as e:
        print(f"Error during download: {e}")
        return False

# Handles the file deletion process by communicating with the server and managing user input and server responses.
def delete_file(client_socket):
    try:
        # Receive the prompt from server
        prompt = client_socket.recv(1024).decode()
        print(prompt, end='')
        
        # Request the filename to delete
        filename = input().strip()
        
        # Send the filename to the server for deletion
        client_socket.sendall(filename.encode())
        
        # Receive server response
        server_response = client_socket.recv(1024).decode()
        
        if server_response == "FILE_NOT_FOUND":
            print("Error: File not found on server.")
            return False
        elif server_response == "FILE_DELETED":
            print(f"File '{filename}' deleted successfully.")
            return True
        else:
            print(f"Server response: {server_response}")
            return False
        
    except Exception as e:
        print(f"Error during file deletion: {e}")
        return False

#Checks if the user enters a valid command (upload, download, delete, or exit) and retries if the input is invalid.
def get_valid_command():
    """Get and validate user command."""
    while True:
        command = input("Enter command (upload/download/delete/exit): ").strip().lower()
        if command in ['upload', 'download', 'delete', 'exit']:
            return command
        elif command:
            print(f"Invalid command: '{command}'. Please enter 'upload', 'download', 'delete' or 'exit'.")

#The entry point of the client program, manages server connection, user authentication (with retries), and continuously handles user commands until exit.
def main():
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTSTP, handle_sigint)
    count=1
    response="Authentication failed."
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('127.0.0.1', 5000))
        while(count<=3 and response=="Authentication failed."):            
            
            print(client_socket.recv(1024).decode(), end='')
            client_socket.sendall(input().encode())
            
            print(client_socket.recv(1024).decode(), end='')
            client_socket.sendall(input().encode())
            
            response = client_socket.recv(1024).decode()
            print(response,'\n')
            if response=="Authentication failed.":
                #count = client_socket.recv(1).decode()
                count+=1
                if count!=4:
                    print("\nTry Again")
            
        
        if response == "Authentication successful.":
            while True:
                try:
                    server_prompt = client_socket.recv(1024).decode()
                    if not server_prompt:
                        print("\nLost connection to server.")
                        break
                    
                    command = get_valid_command()
                    client_socket.sendall(command.encode())
                    
                    if command == 'upload':
                        upload_success = upload_file(client_socket)
                    elif command == 'download':
                        download_success = download_file(client_socket)
                    elif command == 'delete':
                        delete_success = delete_file(client_socket)
                    elif command == 'exit':
                        print("Exiting...")
                        break
                    
                except (BrokenPipeError, ConnectionResetError):
                    print("\nLost connection to server.")
                    break
                except KeyboardInterrupt:
                    print("\nClient shutting down...")
                    try:
                        client_socket.sendall(b'exit')
                    except:
                        pass
                    break
                except Exception as e:
                    print(f"\nUnexpected error: {e}")
                    break
    
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
    except Exception as e:
        print(f"Error: {e}")
    #if count>3:
     #   client_socket.close()
    finally:
        try:
            client_socket.close()
        except:
            pass

if __name__ == "__main__":
    main()
