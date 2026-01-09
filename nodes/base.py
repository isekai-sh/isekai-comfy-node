"""
Base classes and exceptions for Isekai ComfyUI Custom Nodes
"""

from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any


class IsekaiNodeBase(ABC):
    """
    Base class for all Isekai custom nodes.

    This abstract base class provides common functionality and standardization
    across all Isekai nodes, including category naming and type specifications.

    Attributes:
        CATEGORY: The category under which the node appears in ComfyUI
                  Subclasses should set specific categories like:
                  - "Isekai/Dataset" for text and batch processing nodes
                  - "Isekai/Image/Blend" for blending and color adjustment
                  - "Isekai/Image/Effects" for image effects and filters
                  - "Isekai/Image/Transform" for geometric transformations
                  - "Isekai/IO" for filesystem I/O nodes
                  - "Isekai/LLMs" for LLM integration nodes
                  - "Isekai/Upload" for upload/export nodes
    """

    # No default CATEGORY - subclasses must define their own specific category

    @classmethod
    @abstractmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        This method must be implemented by all subclasses to specify the
        input parameters that ComfyUI will display in the node UI.

        Returns:
            Dictionary containing 'required' and/or 'optional' input specifications
        """
        pass


class IsekaiException(Exception):
    """Base exception for all Isekai node errors"""
    pass


class IsekaiValidationError(IsekaiException):
    """Input validation failed"""
    pass


class IsekaiUploadError(IsekaiException):
    """Upload to Isekai API failed"""
    pass


class IsekaiCompressionError(IsekaiException):
    """Image compression failed"""
    pass


class IsekaiConnectionError(IsekaiException):
    """Network connection failed"""
    pass


class IsekaiConfigError(IsekaiException):
    """Configuration error"""
    pass
