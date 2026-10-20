import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE
from typing import Dict, List, Any, Generator, Tuple
import base64

# Minimum dimension in inches to avoid zero-division / negative-extent bugs
_MIN_EXTENT = 0.05


class SlideDecompiler:
    def __init__(self, pptx_path: str):
        self.prs = pptx.Presentation(pptx_path)
        self.slide_width = self.prs.slide_width.inches if self.prs.slide_width else 13.333
        self.slide_height = self.prs.slide_height.inches if self.prs.slide_height else 7.5

    # --- Recursive group traversal -------------------------------------------
    @staticmethod
    def _iter_shapes(
        shapes, parent_left: float = 0.0, parent_top: float = 0.0
    ) -> Generator[Tuple[Any, float, float], None, None]:
        """Yield (shape, offset_left, offset_top) recursively descending groups.

        Enterprise decks heavily nest elements inside GroupShapes; a flat
        iteration over slide.shapes silently drops those children.
        """
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                # Accumulate the group's own position as offset for children
                grp_left = shape.left.inches if shape.left else 0.0
                grp_top = shape.top.inches if shape.top else 0.0
                yield from SlideDecompiler._iter_shapes(
                    shape.shapes,
                    parent_left + grp_left,
                    parent_top + grp_top,
                )
            else:
                yield shape, parent_left, parent_top

    def parse_deck(self) -> List[Dict[str, Any]]:
        parsed_slides = []
        for index, slide in enumerate(self.prs.slides):
            slide_text_accumulator = []
            nodes = []

            # Extract Slide Background Image if present
            bg_image_base64 = None
            try:
                if slide.background and slide.background.fill and slide.background.fill.type == 6: # PICTURE
                    image_blob = slide.background.fill.picture.image.blob
                    bg_image_base64 = base64.b64encode(image_blob).decode('utf-8')
            except Exception:
                pass

            for shape, off_left, off_top in self._iter_shapes(slide.shapes):
                node = self._extract_shape_data(shape, off_left, off_top)
                if node:
                    nodes.append(node)
                    if node.get("type") == "TEXT_CONTAINER" and node.get("paragraphs"):
                        for p in node["paragraphs"]:
                            if p.get("text"):
                                slide_text_accumulator.append(p["text"])

            # Layer order: PICTURES at bottom, containers in middle, text on top
            def _layer_priority(n: Dict[str, Any]) -> int:
                t = n.get("type")
                if t in ("PICTURE", "IMAGE"):
                    return 0
                if t in ("RECTANGLE_SHAPE", "CONTAINER_SHAPE", "OVAL_SHAPE", "LINE_SHAPE", "ARROW_SHAPE"):
                    return 1
                if t in ("TABLE", "CHART"):
                    return 2
                return 3

            nodes.sort(key=_layer_priority)

            full_text = " ".join(slide_text_accumulator)

            slide_ast = {
                "slide_id": index + 1,
                "dimensions": {"width": self.slide_width, "height": self.slide_height},
                "full_text": full_text,
                "bg_image": bg_image_base64,
                "nodes": nodes
            }
            parsed_slides.append(slide_ast)
            
        return parsed_slides

    def _extract_shape_data(
        self, shape, offset_left: float = 0.0, offset_top: float = 0.0
    ) -> Dict[str, Any] | None:
        # Apply parent group offsets and clamp to safe minimums
        left = max(0.0, round((shape.left.inches if shape.left else 0.5) + offset_left, 3))
        top = max(0.0, round((shape.top.inches if shape.top else 0.5) + offset_top, 3))
        width = max(_MIN_EXTENT, round(shape.width.inches if shape.width else 2.0, 3))
        height = max(_MIN_EXTENT, round(shape.height.inches if shape.height else 1.0, 3))

        base_data: Dict[str, Any] = {
            "id": shape.shape_id,
            "x": left,
            "y": top,
            "w": width,
            "h": height,
            "bbox": {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
        }

        # Safe color extraction helpers
        fill_hex = None
        try:
            if shape.fill and shape.fill.type == 1 and hasattr(shape.fill, "fore_color"):
                fill_hex = f"#{shape.fill.fore_color.rgb}"
        except Exception:
            pass
        if fill_hex:
            base_data["fill_color"] = fill_hex

        line_hex = None
        try:
            if shape.line and hasattr(shape.line, "color") and hasattr(shape.line.color, "rgb"):
                line_hex = f"#{shape.line.color.rgb}"
        except Exception:
            pass
        if line_hex:
            base_data["line_color"] = line_hex

        # 1. Check for Picture / Image FIRST (so picture placeholders are not swallowed by has_text_frame)
        is_picture = False
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
                if getattr(shape, "image", None) is not None:
                    is_picture = True
        except Exception:
            pass

        if is_picture:
            try:
                image_bytes = shape.image.blob
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                content_type = getattr(shape.image, "content_type", None) or f"image/{getattr(shape.image, 'ext', 'png')}"
                data_uri = f"data:{content_type};base64,{image_base64}"
                base_data["type"] = "PICTURE"
                base_data["image_src"] = data_uri
                base_data["image_data"] = data_uri
                return base_data
            except Exception:
                pass

        # 2. Text Container Frame
        if shape.has_text_frame:
            paragraphs = []
            is_title_frame = (
                (getattr(shape, "is_placeholder", False) and getattr(shape, "placeholder_format", None) and shape.placeholder_format.type in (1, 3))
                or "title" in (getattr(shape, "name", "") or "").lower()
                or (top < 1.8 and height < 2.0)
            )

            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if "Font Guidance" in txt or "Do not change the template" in txt:
                    continue

                font_color = None
                try:
                    if p.font and hasattr(p.font, "color") and hasattr(p.font.color, "rgb"):
                        font_color = f"#{p.font.color.rgb}"
                except Exception:
                    pass

                # If no explicit font color, resolve contrast-aware color fallback
                if not font_color:
                    font_color = "#FFB81C" if is_title_frame else "#FFFFFF"

                font_name = None
                try:
                    if p.font and p.font.name:
                        font_name = p.font.name
                except Exception:
                    pass
                if not font_name:
                    font_name = "Times New Roman" if is_title_frame else "Arial"

                font_size = p.font.size.pt if p.font and p.font.size else (28.0 if is_title_frame else 12.0)
                bold_val = False if is_title_frame else (p.font.bold if p.font else False)

                paragraphs.append({
                    "text": p.text,
                    "level": p.level,
                    "font_size": font_size,
                    "font_face": font_name,
                    "font_color": font_color,
                    "bold": bold_val,
                    "italic": p.font.italic if p.font else False,
                    "underline": p.font.underline if p.font else False,
                    "align": str(p.alignment) if p.alignment else 'LEFT',
                    "runs": [{"text": r.text} for r in p.runs]
                })

            base_data["type"] = "TEXT_CONTAINER"
            base_data["paragraphs"] = paragraphs
            if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                try:
                    base_data["shape_name"] = str(shape.auto_shape_type)
                except Exception:
                    pass
            return base_data

        # 3. Raw Auto-Shapes / Geometric Shapes / Arrows
        elif shape.shape_type in (MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.FREEFORM):
            shape_enum_str = str(shape.auto_shape_type) if hasattr(shape, 'auto_shape_type') else "RECTANGLE"
            
            # Map Shape Type Enums
            if "ARROW" in shape_enum_str or "CHEVRON" in shape_enum_str:
                base_data["type"] = "ARROW_SHAPE"
            elif "OVAL" in shape_enum_str or "CIRCLE" in shape_enum_str:
                base_data["type"] = "OVAL_SHAPE"
            else:
                base_data["type"] = "RECTANGLE_SHAPE"

            base_data["shape_name"] = shape_enum_str
            return base_data

        # 4. Lines
        elif shape.shape_type == MSO_SHAPE_TYPE.LINE:
            base_data["type"] = "LINE_SHAPE"
            base_data["shape_name"] = "CONNECTOR_LINE"
            return base_data

        # 5. Tables
        elif shape.shape_type == MSO_SHAPE_TYPE.TABLE:
            base_data["type"] = "TABLE"
            base_data["shape_name"] = "TABLE_SHAPE"
            return base_data

        # 6. Charts
        elif shape.shape_type == MSO_SHAPE_TYPE.CHART:
            base_data["type"] = "CHART"
            base_data["shape_name"] = "CHART_SHAPE"
            return base_data

        return None

