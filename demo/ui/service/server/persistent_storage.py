import json
import os
from pathlib import Path
import threading

class PersistentStorage:
    """Simple file-based storage for conversation and agent persistence."""
    
    def __init__(self, storage_dir: str = ".a2a_storage"):
        """Initialize storage with a directory for saving data.
        
        Args:
            storage_dir: Directory to store JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
    
    def save(self, key: str, data) -> None:
        """Save data to a JSON file.
        
        Args:
            key: Identifier for the data (will be the filename)
            data: Data to save (must be JSON serializable)
        """
        file_path = self.storage_dir / f"{key}.json"
        with self._lock:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def load(self, key: str) -> dict:
        """Load data from a JSON file.
        
        Args:
            key: Identifier for the data
            
        Returns:
            Loaded data or empty dict if file doesn't exist
        """
        file_path = self.storage_dir / f"{key}.json"
        if not file_path.exists():
            return {}
        
        with self._lock:
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Handle corrupt files by returning empty data
                return {}


# Helper functions for serializing and deserializing objects
def model_to_dict(model):
    """Convert a model with model_dump to a dictionary."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    elif hasattr(model, "dict"):
        return model.dict()
    else:
        # Try to convert to dict directly
        return dict(model)

def serialize_list(items):
    """Serialize a list of objects to a list of dictionaries."""
    return [model_to_dict(item) for item in items]