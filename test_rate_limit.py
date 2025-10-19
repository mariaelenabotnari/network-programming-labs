import socket
import threading
import time

success_count = 0
fail_count = 0
total_time = 0
lock = threading.Lock()


def create_connection(hostname, port):
    global success_count
    global fail_count

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((hostname, port))
            request = f"GET /fantasy HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
            client_socket.sendall(request.encode())

            response = b""

            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response += chunk

            with lock:
                if b'200 OK' in response:
                    success_count += 1
                elif b'429' in response:
                    fail_count += 1
    except Exception as e:
        print(f"Connection failed: {e}")
        with lock:
            fail_count += 1


def send_requests(hostname, port):
    global total_time
    threads = []
    start_time = time.time()

    while time.time() - start_time < 5:
        thread = threading.Thread(target=create_connection, args=(hostname, port))
        thread.start()
        threads.append(thread)
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    total_time = time.time() - start_time

    return total_time


if __name__ == "__main__":
    total_time = send_requests(hostname="127.0.0.1", port=8080)

    print(f"Total time in which requests were handled: {total_time:.2f} seconds")
    print(f"Total successful requests: {success_count}")
    print(f"Total failed requests: {fail_count}")
    print(f"Throughput: {success_count / total_time:.2f} successful requests per second")
