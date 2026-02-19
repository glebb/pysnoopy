import json
from dataclasses import dataclass, field


REQUIRED_TILE_LAYERS = ("ground", "obstacles", "foreground")


@dataclass
class LevelValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_level_file(
    *,
    level_name: str,
    map_path: str,
    required_layers: tuple[str, ...] = REQUIRED_TILE_LAYERS,
    spawn_object_name: str = "spawn",
    exit_object_name: str = "exit",
    moving_hazard_object_name: str = "moving_hazard",
    required_object_names: tuple[str, ...] = (),
) -> LevelValidationResult:
    result = LevelValidationResult()

    try:
        with open(map_path, "r", encoding="utf-8") as file_handle:
            raw_map = json.load(file_handle)
    except FileNotFoundError:
        result.errors.append(f"{level_name}: map file not found: {map_path}")
        return result
    except json.JSONDecodeError as error:
        result.errors.append(f"{level_name}: invalid JSON in {map_path}: {error}")
        return result

    if raw_map.get("type") != "map":
        result.errors.append(f"{level_name}: map JSON 'type' must be 'map'")

    layers = raw_map.get("layers")
    if not isinstance(layers, list):
        result.errors.append(f"{level_name}: missing 'layers' array")
        return result

    tile_layer_names = {
        layer.get("name")
        for layer in layers
        if isinstance(layer, dict) and layer.get("type") == "tilelayer"
    }

    for required_layer in required_layers:
        if required_layer not in tile_layer_names:
            result.errors.append(
                f"{level_name}: missing required tile layer '{required_layer}'"
            )

    object_layers = [
        layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("type") == "objectgroup"
    ]
    if not object_layers:
        result.warnings.append(
            f"{level_name}: no object layer found (optional but recommended for '{spawn_object_name}'/'{exit_object_name}')"
        )
        return result

    object_names = {
        obj.get("name")
        for layer in object_layers
        for obj in layer.get("objects", [])
        if isinstance(obj, dict)
    }

    if spawn_object_name not in object_names:
        result.warnings.append(
            f"{level_name}: object '{spawn_object_name}' not found; fallback spawn logic will be used"
        )

    if exit_object_name not in object_names:
        result.warnings.append(
            f"{level_name}: object '{exit_object_name}' not found; right-edge transition fallback will be used"
        )

    for required_object_name in required_object_names:
        if required_object_name not in object_names:
            result.errors.append(
                f"{level_name}: missing required object '{required_object_name}'"
            )

    for layer in object_layers:
        for obj in layer.get("objects", []):
            if not isinstance(obj, dict):
                continue
            if obj.get("name") != moving_hazard_object_name:
                continue

            width = obj.get("width", 0)
            height = obj.get("height", 0)
            if float(width) <= 0 or float(height) <= 0:
                result.errors.append(
                    f"{level_name}: object '{moving_hazard_object_name}' must have positive width and height"
                )
                continue

            properties = obj.get("properties", [])
            if not isinstance(properties, list):
                continue
            property_values = {
                item.get("name"): item.get("value")
                for item in properties
                if isinstance(item, dict)
            }
            for speed_property in ("speed_x", "speed_y"):
                if speed_property in property_values:
                    value = property_values[speed_property]
                    if value is None:
                        result.errors.append(
                            f"{level_name}: object '{moving_hazard_object_name}' has missing '{speed_property}' value"
                        )
                        continue
                    try:
                        float(value)
                    except (TypeError, ValueError):
                        result.errors.append(
                            f"{level_name}: object '{moving_hazard_object_name}' has non-numeric '{speed_property}'"
                        )

    return result
