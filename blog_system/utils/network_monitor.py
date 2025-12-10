import time
import threading
from datetime import datetime
from models import db, NetworkStats

class NetworkMonitor:
    def __init__(self, app):
        self.app = app
        self.request_times = []
        self.active_connections = 0
        self.lock = threading.Lock()
        
    def record_request(self):
        with self.lock:
            current_time = time.time()
            self.request_times.append(current_time)
            self.active_connections += 1
            
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
    
    def request_completed(self):
        with self.lock:
            self.active_connections = max(0, self.active_connections - 1)
    
    def get_current_latency(self):
        if len(self.request_times) > 10:
            return 50 + (len(self.request_times) % 20)
        return 50
    
    def get_current_throughput(self):
        cutoff_time = time.time() - 60
        recent_requests = [t for t in self.request_times if t > cutoff_time]
        return len(recent_requests)
    
    def get_active_connections(self):
        return self.active_connections
    
    def _save_stats_to_db(self):
        with self.lock:
            stats = NetworkStats(
                latency=self.get_current_latency(),
                throughput=self.get_current_throughput(),
                active_connections=self.active_connections
            )
            
            try:
                db.session.add(stats)
                db.session.commit()
            except Exception as e:
                print(f"保存网络统计失败: {e}")
                db.session.rollback()
    
    def start_background_task(self):
        def stats_collector():
            while True:
                time.sleep(60)
                with self.app.app_context():
                    self._save_stats_to_db()
        
        thread = threading.Thread(target=stats_collector)
        thread.daemon = True
        thread.start()