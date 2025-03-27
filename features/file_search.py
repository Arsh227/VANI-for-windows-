import os
import shutil
from datetime import datetime
import json
from pathlib import Path
import pyautogui
import time

class FileManager:
    def __init__(self):
        # Common directories
        self.home = str(Path.home())
        self.downloads = os.path.join(self.home, "Downloads")
        self.documents = os.path.join(self.home, "Documents")
        self.pictures = os.path.join(self.home, "Pictures")
        
        # Search history
        self.history_file = "data/search_history.json"
        self.search_history = self.load_history()
        
        self.last_search_results = []  # Store last search results
        
        print("File management system initialized!")

    def load_history(self):
        """Load search history"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}

    def save_history(self):
        """Save search history"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.search_history, f)
        except Exception as e:
            print(f"Error saving history: {str(e)}")

    def search_files(self, query, location=None):
        """Search for files using keywords"""
        try:
            if not location:
                location = self.home
            
            results = []
            keywords = query.lower().split()  # Split query into keywords
            
            # Record search
            self.search_history[datetime.now().strftime("%Y-%m-%d %H:%M:%S")] = {
                'query': query,
                'location': location
            }
            self.save_history()
            
            # Walk through directory
            for root, dirs, files in os.walk(location):
                for file in files:
                    file_lower = file.lower()
                    # Check if ALL keywords are in the filename
                    if all(keyword in file_lower for keyword in keywords):
                        full_path = os.path.join(root, file)
                        results.append({
                            'name': file,
                            'path': full_path,
                            'size': os.path.getsize(full_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                        })
            
            return results
        except Exception as e:
            return f"Error searching files: {str(e)}"

    def organize_downloads(self):
        """Organize downloads folder by file type"""
        try:
            if not os.path.exists(self.downloads):
                return "Downloads folder not found"
            
            # File type categories
            categories = {
                'Images': ['.jpg', '.jpeg', '.png', '.gif'],
                'Documents': ['.pdf', '.doc', '.docx', '.txt'],
                'Audio': ['.mp3', '.wav', '.flac'],
                'Video': ['.mp4', '.avi', '.mkv'],
                'Archives': ['.zip', '.rar', '.7z']
            }
            
            moved_files = 0
            for filename in os.listdir(self.downloads):
                file_path = os.path.join(self.downloads, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    
                    # Find category
                    for category, extensions in categories.items():
                        if ext in extensions:
                            # Create category folder
                            category_path = os.path.join(self.downloads, category)
                            os.makedirs(category_path, exist_ok=True)
                            
                            # Move file
                            shutil.move(file_path, os.path.join(category_path, filename))
                            moved_files += 1
                            break
            
            return f"Organized {moved_files} files in Downloads folder"
        except Exception as e:
            return f"Error organizing downloads: {str(e)}"

    def find_duplicates(self, directory=None):
        """Find duplicate files in directory"""
        try:
            if not directory:
                directory = self.downloads
            
            # Store file sizes and hashes
            files_by_size = {}
            duplicates = []
            
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    filesize = os.path.getsize(filepath)
                    
                    if filesize in files_by_size:
                        # Potential duplicate found
                        for existing in files_by_size[filesize]:
                            if self._compare_files(filepath, existing):
                                duplicates.append({
                                    'original': existing,
                                    'duplicate': filepath
                                })
                    else:
                        files_by_size[filesize] = [filepath]
            
            return duplicates
        except Exception as e:
            return f"Error finding duplicates: {str(e)}"

    def _compare_files(self, file1, file2):
        """Compare two files for equality"""
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                while True:
                    chunk1 = f1.read(8192)
                    chunk2 = f2.read(8192)
                    if chunk1 != chunk2:
                        return False
                    if not chunk1:
                        return True
        except:
            return False 

    def open_file_explorer(self):
        """Open File Explorer and offer search"""
        try:
            # Press Windows key + E to open File Explorer
            pyautogui.hotkey('win', 'e')
            time.sleep(1)  # Wait for Explorer to open
            
            # Ask if user wants to search
            return "File Explorer opened. Would you like to search for a specific file?"
        except Exception as e:
            return f"Error opening File Explorer: {str(e)}"

    def search_in_explorer(self, query):
        """Search for files in File Explorer using keywords"""
        try:
            # Press Ctrl + F to open search
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            # Type search query
            pyautogui.write(query)
            time.sleep(1)
            
            # Get search results using keyword matching
            results = self.search_files(query)
            self.last_search_results = results  # Store results for later use
            
            if results:
                result_text = f"Found {len(results)} files matching keywords '{query}':\n"
                for i, file in enumerate(results[:5], 1):
                    rel_path = os.path.relpath(file['path'], self.home)
                    result_text += f"{i}. {file['name']}\n   Location: ~/{rel_path}\n"
                return result_text
            return f"No files found matching keywords '{query}'"
        except Exception as e:
            return f"Error searching: {str(e)}"

    def open_documents(self):
        """Open Documents folder"""
        try:
            os.startfile(self.documents)
            return "Opened Documents folder"
        except Exception as e:
            return f"Error opening Documents: {str(e)}"

    def open_downloads(self):
        """Open Downloads folder"""
        try:
            os.startfile(self.downloads)
            return "Opened Downloads folder"
        except Exception as e:
            return f"Error opening Downloads: {str(e)}"

    def open_pictures(self):
        """Open Pictures folder"""
        try:
            os.startfile(self.pictures)
            return "Opened Pictures folder"
        except Exception as e:
            return f"Error opening Pictures: {str(e)}"

    def open_file_by_number(self, number):
        """Open a file from the last search results by its number"""
        try:
            if not self.last_search_results or number < 1 or number > len(self.last_search_results):
                return "Invalid file number"
            
            file_path = self.last_search_results[number-1]['path']
            os.startfile(file_path)
            return f"Opened {os.path.basename(file_path)}"
        except Exception as e:
            return f"Error opening file: {str(e)}" 