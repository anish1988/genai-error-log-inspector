import os, time
import schedule
from concurrent.futures import ThreadPoolExecutor

class Scheduler:
    def __init__(self, every_minutes: int, parallel: bool):
        self.every = every_minutes
        self.parallel = parallel

    def run_forever(self, job):
        schedule.every(self.every).minutes.do(job)
        job()  # run immediately
        while True:
            schedule.run_pending()
            time.sleep(1)

    def run_batch(self, callables):
        if self.parallel and len(callables) > 1:
            with ThreadPoolExecutor(max_workers=min(8, len(callables))) as pool:
                for fn in callables: pool.submit(fn)
        else:
            for fn in callables: fn()
