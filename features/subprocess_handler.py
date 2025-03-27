import threading
import time
import queue
import subprocess
import os
from typing import List, Dict

class SubprocessHandler:
    def __init__(self, ai_services, conversation_handler):
        self.ai_services = ai_services
        self.conversation = conversation_handler
        self.task_queue = queue.Queue()
        self.is_processing = False
        self.current_tasks = []
        self.processes = {}  # Track running processes
        
        # Conjunctions that indicate multi-tasking
        self.task_separators = {
            "and": "parallel",    # Execute tasks simultaneously
            "then": "sequential", # Execute tasks in order
            "while": "parallel",  # Execute tasks simultaneously
            "after": "sequential",# Execute tasks in order
            "or": "choice",       # Ask user which task to execute
            "followed by": "sequential"
        }

    def run_system_command(self, command: str) -> str:
        """Run a system command using subprocess"""
        try:
            # Get system path
            system_path = os.environ.get('PATH', '')
            command_path = os.path.join(os.environ.get('WINDIR', ''), command)
            
            # Run command and capture output
            process = subprocess.Popen(
                command_path if os.path.exists(command_path) else command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={'PATH': system_path}
            )
            
            # Store process for potential termination
            self.processes[command] = process
            
            # Get output with timeout
            stdout, stderr = process.communicate(timeout=30)
            
            # Remove from tracking
            self.processes.pop(command, None)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                return f"Error: {stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            # Kill process if it times out
            if command in self.processes:
                self.processes[command].kill()
                self.processes.pop(command)
            return "Command timed out"
            
        except Exception as e:
            return f"Command error: {str(e)}"

    def parse_complex_command(self, command: str) -> List[str]:
        """Parse complex command into individual tasks"""
        tasks = []
        current_command = ""
        
        # First split by sequential operators
        for separator in ["then", "after", "followed by"]:
            if separator in command.lower():
                parts = command.lower().split(separator)
                tasks.extend([part.strip() for part in parts])
                return tasks
                
        # Then split by parallel operators
        for separator in ["and", "while"]:
            if separator in command.lower():
                parts = command.lower().split(separator)
                tasks.extend([part.strip() for part in parts])
                return tasks
                
        # If no separators found, treat as single task
        tasks.append(command)
        return tasks

    def execute_tasks(self, tasks: List[str]) -> str:
        """Execute multiple tasks based on their type"""
        try:
            self.is_processing = True
            results = []
            
            # Determine execution type from the original command
            if any(word in tasks[0] for word in ["then", "after", "followed by"]):
                # Sequential execution
                for task in tasks:
                    if task.startswith("run "):
                        # Handle system commands
                        cmd = task.replace("run ", "", 1)
                        result = self.run_system_command(cmd)
                    else:
                        result = self.conversation.process_user_input(task)
                    results.append(f"✓ {task}: {result}")
                    time.sleep(0.5)
                    
            elif any(word in tasks[0] for word in ["and", "while"]):
                # Parallel execution using threads and subprocesses
                threads = []
                task_results = queue.Queue()
                
                def execute_task(task):
                    try:
                        if task.startswith("run "):
                            cmd = task.replace("run ", "", 1)
                            result = self.run_system_command(cmd)
                        else:
                            result = self.conversation.process_user_input(task)
                        task_results.put((task, result))
                    except Exception as e:
                        task_results.put((task, f"Error: {str(e)}"))
                
                # Start all tasks in parallel
                for task in tasks:
                    thread = threading.Thread(
                        target=execute_task,
                        args=(task,),
                        daemon=True
                    )
                    threads.append(thread)
                    thread.start()
                
                # Wait for all tasks to complete
                for thread in threads:
                    thread.join()
                
                # Collect results
                while not task_results.empty():
                    task, result = task_results.get()
                    results.append(f"✓ {task}: {result}")
            
            return "\n".join(results)
            
        except Exception as e:
            print(f"Task execution error: {e}")
            return f"Error executing tasks: {str(e)}"
        finally:
            self.is_processing = False
            # Cleanup any remaining processes
            for proc in self.processes.values():
                try:
                    proc.kill()
                except:
                    pass
            self.processes.clear()

    def handle_complex_command(self, command: str) -> str:
        """Main entry point for handling complex commands"""
        try:
            # Parse the command into tasks
            tasks = self.parse_complex_command(command)
            
            if not tasks:
                return "No valid tasks found in command"
            
            # Execute the tasks
            if len(tasks) > 1:
                print(f"\n🔄 Processing {len(tasks)} tasks...")
                return self.execute_tasks(tasks)
            else:
                return self.conversation.process_user_input(tasks[0])
                
        except Exception as e:
            print(f"Complex command error: {e}")
            return f"Error processing complex command: {str(e)}" 