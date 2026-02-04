#!/usr/bin/env python3
"""
Watchdog - Ippoc System Monitor
Restarts failed services and maintains organism health
"""

import time
import subprocess
import json
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Watchdog:
    def __init__(self):
        self.services = {
            'mnemosyne': {'port': 8001, 'healthy': False},
            'soma': {'port': 8002, 'healthy': False},
            'cortex': {'port': 8003, 'healthy': False},
            'gateway': {'port': 8080, 'healthy': False}
        }
        
    def check_health(self, service: str, port: int) -> bool:
        """Check if service is responding"""
        try:
            result = subprocess.run(
                ['curl', '-f', f'http://localhost:{port}/health'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
            
    def restart_service(self, service: str) -> bool:
        """Restart a failed service"""
        logger.info(f"🔄 Restarting {service}...")
        try:
            subprocess.run(['docker', 'restart', f'ippoc-{service}'], check=True)
            logger.info(f"✅ {service} restarted successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error(f"❌ Failed to restart {service}")
            return False
            
    def monitor(self):
        """Main monitoring loop"""
        logger.info("🐕 Watchdog activated - Monitoring Ippoc organs")
        
        while True:
            for service, config in self.services.items():
                healthy = self.check_health(service, config['port'])
                
                if not healthy and config['healthy']:
                    logger.warning(f"⚠️  {service} is unhealthy")
                    self.restart_service(service)
                elif healthy and not config['healthy']:
                    logger.info(f"💚 {service} is now healthy")
                    
                config['healthy'] = healthy
                
            time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    watchdog = Watchdog()
    try:
        watchdog.monitor()
    except KeyboardInterrupt:
        logger.info("Watchdog shutting down...")