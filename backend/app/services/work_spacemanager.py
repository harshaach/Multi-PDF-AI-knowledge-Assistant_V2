from app.services.embedding_services import EmbeddingService


class Workspace:
    """
    Represents one chat workspace.
    Each chat has its own EmbeddingService and document list.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.documents: list[str] = []


class WorkspaceManager:
    """
    Manages all chat workspaces.
    """

    def __init__(self):
        self.workspaces: dict[str, Workspace] = {}

    def get_workspace(self, chat_id: str) -> Workspace:
        """
        Returns the workspace for a chat.
        Creates one if it doesn't exist.
        """
        if chat_id not in self.workspaces:
            self.workspaces[chat_id] = Workspace()

        return self.workspaces[chat_id]

    def delete_workspace(self, chat_id: str):
        """
        Removes a workspace completely.
        """
        if chat_id in self.workspaces:
            del self.workspaces[chat_id]

    def workspace_exists(self, chat_id: str) -> bool:
        return chat_id in self.workspaces


workspace_manager = WorkspaceManager()