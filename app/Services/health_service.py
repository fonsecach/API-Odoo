import time
from datetime import datetime


class HealthCheck:
    def __init__(self):
        self.status = 'ok'
        self.version = '0.1.0'
        self.start_time = time.time()

    def get_health_check(self) -> dict:
        return {
            'status': 'healthy',
            'version': self.version,
            'timestamp': datetime.now(),
            'uptime': time.time() - self.start_time,
        }

    def get_ping_status(self) -> dict:
        return {'status': 'ok'}
