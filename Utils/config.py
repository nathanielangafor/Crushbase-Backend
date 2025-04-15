"""
Configuration file containing directory paths and other constants.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Directory paths
FILES_DIRECTORY: str = "SystemFiles"
FILES_DIRECTORY_PATH: Path = Path(FILES_DIRECTORY)

def create_response(
    success: bool,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create a standardized response dictionary.
    
    Args:
        success: Boolean indicating if the operation was successful
        data: Optional data to include in the response
        error: Optional error message if the operation failed
        **kwargs: Additional fields to include in the response
        
    Returns:
        Dict containing the standardized response format
    """
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success and data is not None:
        response["data"] = data
    elif not success and error is not None:
        response["error"] = error
        
    response.update(kwargs)
    return response