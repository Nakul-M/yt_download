import os
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['default']
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    raise ValueError("Missing REDIS_URL environment variable")

conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
