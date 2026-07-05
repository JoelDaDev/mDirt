"""
Pure data model for an mDirt project.
"""


class PackDetails:
    __slots__ = ("name", "namespace", "description", "author", "version")

    def __init__(self, name="", namespace="", description="", author="", version=""):
        self.name = name
        self.namespace = namespace
        self.description = description
        self.author = author
        self.version = version

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "namespace": self.namespace,
            "description": self.description,
            "author": self.author,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackDetails":
        return cls(
            name=d.get("name", ""),
            namespace=d.get("namespace", ""),
            description=d.get("description", ""),
            author=d.get("author", ""),
            version=d.get("version", ""),
        )


class Project:
    """
    Holds all runtime state for an open project.

    Element data (blocks, items, etc.) are stored as plain dicts whose
    structure matches the JSON saved to disk — booleans are stored as the
    strings "true"/"false" to preserve backwards-compatibility with the
    generation modules and existing save files.

    Scratch state (textures being picked for the currently open editor) is
    stored here so controllers can share it with the window when needed.

    `trees` maps element-type names to their QTreeWidgetItem header nodes so
    that controllers can add / remove rows without touching the window.
    """

    def __init__(self):
        # ── Pack metadata ─────────────────────────────────────────────────
        self.pack_details = PackDetails()
        self.data_format: float = 0.0
        self.resource_format: float = 0.0
        self.mc_data: dict = {}
        self.version_json: dict = {}
        self.header: str = ""

        # ── Element collections ───────────────────────────────────────────
        self.blocks: dict = {}
        self.items: dict = {}
        self.recipes: dict = {}
        self.paintings: dict = {}
        self.structures: dict = {}
        self.equipment: dict = {}
        self.archetypes: dict = {}

        # ── Scratch state for the currently open editor ───────────────────
        self.block_textures: dict = {}       # BlockFace → abs path str
        self.item_texture: str | None = None
        self.painting_texture: str | None = None
        self.structure_path: str | None = None
        self.equipment_textures: dict = {}   # slot name → abs path str
        self.equipment_models: dict = {}     # key ("h", "h_l", …) → abs path str

        # ── Qt tree widget headers (set by Window after UI is built) ──────
        # Keyed by element type name; values are QTreeWidgetItem instances.
        self.trees: dict = {}

        # ── Status flags ──────────────────────────────────────────────────
        self.is_loaded: bool = False
        self.unsaved_changes: bool = False

    def reset_scratch(self):
        """Clear all editor scratch state between elements."""
        self.block_textures = {}
        self.item_texture = None
        self.painting_texture = None
        self.structure_path = None
        self.equipment_textures = {}
        self.equipment_models = {}

    def reset_elements(self):
        """Clear all element collections (called when opening a new project)."""
        self.blocks = {}
        self.items = {}
        self.recipes = {}
        self.paintings = {}
        self.structures = {}
        self.equipment = {}
        self.archetypes = {}
        self.reset_scratch()
