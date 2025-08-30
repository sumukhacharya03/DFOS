# DFOS: Distributed File Orchestration and Synchronization

A multi-client file transfer system built with Python, featuring a robust client-server architecture for handling concurrent file operations.

## Architechture

<img width="579" height="104" alt="image" src="https://github.com/user-attachments/assets/31d7bff5-edae-4666-8ca9-ed3adab31066" />


## Features

* **User Authentication:** Secure client login based on a predefined username and password list.
* **Concurrent Client Handling:** Uses a thread pool to manage multiple client connections simultaneously without data loss.
* **User-Specific Storage:** Automatically creates and manages a dedicated storage directory for each authenticated user.
* **File Operations:**
    * **Upload:** Securely upload files to the user's dedicated directory.
    * **Download:** Download files from the server.
    * **Preview:** View the first 1024 bytes of a file without downloading the entire content.
    * **Delete:** Remove files from the user's server-side directory.
* **Performance Logging:** Tracks server performance, including connections and file transfer metrics, to a log file.
* **Graceful Shutdown:** A signal handler ensures the server can shut down safely, logging final performance stats.

## Technologies Used

* **Python 3**
* **socket:** For core network communication.
* **threading & `ThreadPoolExecutor`:** For handling multiple clients concurrently.
* **os:** For file system operations on the server.
* **logging:** For detailed performance and event logging.
* **psutil:** To monitor system resources (CPU/Memory) on shutdown.

## Running the System

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sumukhacharya03/DFOS.git
    cd DFOS
    ```

2.  **Configure Users:**
    Edit the `id_passwd.txt` file to add or change user credentials.
    ```
    user1:password123
    user2:newpassword
    ```

3.  **Start the Server:**
    Open a terminal and run the server script.
    ```bash
    python server.py
    ```
    The server will start listening on port 5000.

## Co-Authors

1. Vandana J
2. V Shreya Sivani
3. Trishita Umapathi

5.  **Run the Client:**
    Open a second terminal to run the client.
    ```bash
    python client.py
    ```
    You will be prompted for your username and password to connect.
