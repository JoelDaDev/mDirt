import json
import os

class ArchetypeGenerator:
    def __init__(self, namespaceDirectory, packNamespace, archetypes):
        self.namespaceDirectory = namespaceDirectory
        self.packNamespace = packNamespace
        self.archetypes = archetypes

    def generate(self):
        archetypes_dir = os.path.join(self.namespaceDirectory, "sulfur_cube_archetypes")

        for key, archetype in self.archetypes.items():
            data = {
                "attribute_modifiers": [
                    {
                        "attribute": attr["attribute"],
                        "id": attr["id"],
                        "amount": attr["amount"],
                        "operation": attr["operation"]
                    }
                    for attr in archetype.get("attributes", {}).values()
                ],
                "buoyant": archetype["buoyant"] == "true",
                "items": archetype["item"],
                "knockback_modifiers": {
                    "horizontal_power": archetype["horizontal_power"],
                    "vertical_power": archetype["vertical_power"]
                }
            }

            if "explosion" in archetype:
                data["explosion"] = {
                    "causes_fire": archetype["explosion"]["causes_fire"] == "true",
                    "fuse": archetype["explosion"]["fuse"],
                    "power": archetype["explosion"]["power"]
                }

            if "contact_damage" in archetype:
                data["contact_damage"] = {
                    "amount": archetype["contact_damage"]["amount"],
                    "attribute_to_source": archetype["contact_damage"]["attr_to_source"] == "true",
                    "damage_type": archetype["contact_damage"]["damage_type"]
                }

            with open(os.path.join(archetypes_dir, f"{key}.json"), "w") as f:
                json.dump(data, f, indent=4)
