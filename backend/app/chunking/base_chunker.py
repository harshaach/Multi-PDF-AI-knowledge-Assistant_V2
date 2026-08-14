from abc import ABC, abstractmethod
from typing import List

from app.models.chunk import Chunk
from app.models.page import Page


class BaseChunker(ABC):
    """
    Abstract base class for all chunking strategies.
    """

    @abstractmethod
    def chunk_page(self, page: Page) -> List[Chunk]:
        """
        Convert a Page into a list of Chunk objects.
        """
        pass