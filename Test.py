import argparse
import os
import socket
import threading
import time


def create_connection(hostname, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((hostname, port))
        request = f"GET / HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
        client_socket.sendall(request.encode())
        client_socket.recv(4096)


def send_10_requests(hostname, port):
    threads = []
    start_time = time.time()

    for _ in range(10):
        thread = threading.Thread(target=create_connection, args=(hostname, port))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    total_time = time.time() - start_time
    print(f"All 10 requests handled in {total_time:.2f} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Test for checking the amount of time it takes the server to handle 10 concurrent "
                                     "requests.")
    parser.add_argument('server_host', help='Server hostname or IP')
    parser.add_argument('server_port', type=int, help='Server port number')

    args = parser.parse_args()

    send_10_requests(args.server_host, args.server_port)
