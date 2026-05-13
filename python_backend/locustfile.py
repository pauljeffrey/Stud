"""
Optional load smoke: locust -f locustfile.py --host=http://127.0.0.1:8000
"""
from locust import HttpUser, between, task


class HealthUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health(self):
        self.client.get("/health")
