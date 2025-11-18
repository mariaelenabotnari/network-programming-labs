import threading
import time
import random
import requests
import os


def replicate_to_followers(key, value, followers_urls):
    MIN_DELAY = float(os.getenv("MIN_DELAY", 0.0001))
    MAX_DELAY = float(os.getenv("MAX_DELAY", 0.01))
    WRITE_QUORUM = int(os.getenv("WRITE_QUORUM", 1))

    confirmations = 0
    confirmations_lock = threading.Lock()
    threads = []

    quorum_event = threading.Event()

    def send_replication(url):
        nonlocal confirmations

        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

        try:
            response = requests.post(url, json={"key": key, "value": value}, timeout=1)

            if response.status_code == 200:
                with confirmations_lock:
                    confirmations += 1

                    if confirmations >= WRITE_QUORUM:
                        quorum_event.set()
        except Exception:
            pass

    for url in followers_urls:
        thread = threading.Thread(target=send_replication, args=(url,))
        threads.append(thread)
        thread.start()

    quorum_event.wait(timeout=2)

    if confirmations >= WRITE_QUORUM:
        return True
    else:
        return False
