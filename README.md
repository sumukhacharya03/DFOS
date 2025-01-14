# DFOS
Distributed File Orchestration and Synchronization: Multi-Node Data-Transfer-Framework for Linux

# Overview of the Project:

We designed and implemented a multi-client file transfer system using a client-server model in Python. The server can handle multiple clients simultaneously. The server should allow the clients to upload, download, view, and delete files from a server-side directory, and respond to multiple concurrent requests without crashing or losing data.

![image](https://github.com/user-attachments/assets/9ce97213-99bc-42c2-8a3a-c982df705d71)

# Background:

Modern file transfer systems, such as FTP(File Transfer Protocol), are widely used for transferring data between clients and servers in networked environments. Such systems need to support various functionalities like user authentication, file uploading, downloading, and secure data management. Additionally, the system must handle multiple clients simultaneously without sacrificing performance or data integrity. 


# What are we doing in this Project?

- Authenticate clients based on a predefined list of usernames and passwords.
- Allow authenticated clients to perform the following actions:
  - **Upload Files**:  After authenticating, a client can upload a file to the server by providing the file name. The server should save the file in a directory specific to the client (e.g., /server_storage/<username>).
  - **Download Files**: The client can request a file to download from their directory on the server. If the file exists, the server should send it; otherwise, an error message is returned
  - **View Files**: The client can request a preview of the first 1024 bytes of any file in their directory.
  - **Delete Files**: The client can delete any file from their directory. Upon successful deletion, the server should confirm the operation.
  - **List Files**: Clients can request a list of all files stored in their directory. The server should send a list of file names in that directory.
- Handle multiple clients concurrently, without interference between them.
- Support a robust signal handling mechanism that ensures the server can safely shut down while maintaining data integrity.

# Future Work:

As part of future development, the following features can be added:

- **SSL/TLS Support**: For secure communication between the client and server.
- **Logging and Auditing**: To track client actions and server performance over time.
- **Thread-based Implementation**: Instead of forking processes, a thread-based approach could be explored for more efficient resource management.
