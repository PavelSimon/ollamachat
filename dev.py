#!/usr/bin/env python3
"""
Development server with auto-restart functionality for OLLAMA Chat
This script provides a development environment with:
- Auto-restart on file changes
- Enhanced logging for development
- Proper environment setup
- Database initialization
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class DevelopmentReloadHandler(FileSystemEventHandler):
    """Handler for file system events that triggers server restart"""
    
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback
        self.last_restart = 0
        self.restart_delay = 1  # Minimum seconds between restarts
        
        # File patterns to watch
        self.watch_patterns = {
            '.py', '.html', '.css', '.js', '.json', '.toml', '.md'
        }
        
        # Directories to ignore
        self.ignore_dirs = {
            '__pycache__', '.git', 'node_modules', 'instance', 'logs', '.pytest_cache'
        }
    
    def should_restart(self, file_path):
        """Determine if file change should trigger restart"""
        path = Path(file_path)
        
        # Ignore certain directories
        if any(ignore_dir in path.parts for ignore_dir in self.ignore_dirs):
            return False
        
        # Only watch specific file extensions
        if path.suffix not in self.watch_patterns:
            return False
            
        # Ignore temporary files
        if path.name.startswith('.') or path.name.endswith('~'):
            return False
            
        return True
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if self.should_restart(event.src_path):
            current_time = time.time()
            if current_time - self.last_restart > self.restart_delay:
                self.last_restart = current_time
                relative_path = Path(event.src_path).relative_to(project_root)
                print(f"\n[CHANGED] File changed: {relative_path}")
                self.restart_callback()

class DevelopmentServer:
    """Development server with auto-restart capabilities"""
    
    def __init__(self):
        self.process = None
        self.observer = None
        self.should_exit = False
        
    def setup_environment(self):
        """Setup development environment variables"""
        print("[SETUP] Setting up development environment...")
        
        # Set development environment
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '0'  # Disable Flask's built-in reloader since we're using watchdog
        
        # Enable console logging for development
        os.environ['LOG_TO_CONSOLE'] = 'true'
        
        # Set default secret key for development (will be auto-generated if not set)
        if not os.environ.get('SECRET_KEY'):
            os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
        
        # Set default database URL for development
        if not os.environ.get('DATABASE_URL'):
            instance_dir = project_root / 'instance'
            instance_dir.mkdir(exist_ok=True)
            os.environ['DATABASE_URL'] = f'sqlite:///{instance_dir}/chat.db'
        
        # Set default OLLAMA host
        if not os.environ.get('DEFAULT_OLLAMA_HOST'):
            os.environ['DEFAULT_OLLAMA_HOST'] = 'http://localhost:11434'
        
        print("[OK] Environment configured for development")
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print("[DEPS] Checking dependencies...")
        
        try:
            import flask
            import flask_login
            import flask_wtf
            import flask_limiter
            import requests
            import marshmallow
            print("[OK] All core dependencies available")
        except ImportError as e:
            print(f"[ERROR] Missing dependency: {e}")
            print("[TIP] Run: uv sync --dev")
            return False
        
        # Check for development-specific dependencies
        try:
            import watchdog
            print("[OK] Development dependencies available")
        except ImportError:
            print("[WARNING]  Missing watchdog for auto-restart")
            print("[TIP] Installing watchdog...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)
                print("[OK] Watchdog installed successfully")
            except subprocess.CalledProcessError:
                print("[ERROR] Failed to install watchdog")
                return False
                
        return True
    
    def initialize_database(self):
        """Initialize the database for development"""
        print("[DB]  Initializing database...")
        try:
            from app import init_db
            init_db()
            print("[OK] Database initialized successfully")
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
            return False
        return True
    
    def start_flask_server(self):
        """Start the Flask development server"""
        if self.process:
            self.stop_flask_server()
        
        print("[START] Starting Flask development server...")
        
        # Use a simpler approach to start the Flask app
        cmd = [
            sys.executable, 'app.py'
        ]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            # Wait a moment to check if process started successfully
            time.sleep(0.5)
            if self.process.poll() is not None:
                print(f"[ERROR] Flask server exited immediately with code {self.process.returncode}")
                return False
                
            print("[OK] Flask server started successfully")
            print("[SERVER] Server running at: http://127.0.0.1:5000")
            print("[INFO] Auto-restart enabled - modify files to trigger restart")
            print("[STOP]  Press Ctrl+C to stop")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start Flask server: {e}")
            return False
    
    def stop_flask_server(self):
        """Stop the Flask development server"""
        if self.process:
            print("[STOP]  Stopping Flask server...")
            try:
                if sys.platform == "win32":
                    # On Windows, send CTRL_BREAK_EVENT to the process group
                    import signal
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.process.terminate()
                    
                # Wait for graceful shutdown
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("[KILL]  Force killing Flask server...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"[WARNING] Error stopping server: {e}")
                try:
                    self.process.kill()
                    self.process.wait()
                except:
                    pass
            finally:
                self.process = None
    
    def setup_file_watcher(self):
        """Setup file system watcher for auto-restart"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        print("[WATCH] Setting up file watcher...")
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            self.observer = Observer()
            handler = DevelopmentReloadHandler(self.restart_server)
            
            # Watch the main project directory
            self.observer.schedule(handler, str(project_root), recursive=True)
            self.observer.start()
            print("[OK] File watcher active")
            
        except ImportError:
            print("[WARNING]  Watchdog not available - auto-restart disabled")
            print("[TIP] Install with: pip install watchdog")
    
    def restart_server(self):
        """Restart the Flask server"""
        if not self.should_exit:
            print("[RESTART] Restarting Flask server...")
            self.stop_flask_server()
            time.sleep(1)  # Brief pause to ensure clean shutdown
            if not self.should_exit:  # Check again in case of interrupt during restart
                self.start_flask_server()
    
    def run(self):
        """Main development server run loop"""
        print("OLLAMA Chat Development Server")
        print("=" * 40)
        
        # Setup environment
        self.setup_environment()
        
        # Check dependencies
        if not self.check_dependencies():
            return 1
        
        # Initialize database
        if not self.initialize_database():
            return 1
        
        # Setup file watcher
        self.setup_file_watcher()
        
        # Start Flask server
        if not self.start_flask_server():
            return 1
        
        try:
            # Keep the main process alive and monitor for restarts
            while not self.should_exit:
                if self.process and self.process.poll() is None:
                    # Process is running, read output if available
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            print(line.rstrip())
                    except (ValueError, AttributeError):
                        # Handle case when process is restarted
                        pass
                elif self.process and self.process.poll() is not None:
                    # Process has exited, check if we should restart
                    if not self.should_exit:
                        print("[WARNING] Flask server exited unexpectedly, restarting...")
                        time.sleep(1)
                        self.start_flask_server()
                else:
                    # No process running
                    time.sleep(0.1)
                
                # Small delay to prevent busy waiting
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n[STOP]  Shutting down development server...")
            self.should_exit = True
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Clean up resources"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.stop_flask_server()
        print("[OK] Development server stopped")

def main():
    """Main entry point"""
    server = DevelopmentServer()
    return server.run()

if __name__ == '__main__':
    sys.exit(main())