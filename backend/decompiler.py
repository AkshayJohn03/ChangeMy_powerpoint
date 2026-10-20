import base64
import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.dml import MSO_FILL
from typing import Dict, List, Any, Optional, Generator, Tuple

try:
    from brandmorph.engine.archetype_engine import SlideGraphClassifier
except Exception:
    try:
        from .brandmorph.engine.archetype_engine import SlideGraphClassifier
    except Exception:
        try:
            from backend.brandmorph.engine.archetype_engine import SlideGraphClassifier
        except Exception:
            SlideGraphClassifier = None

# Minimum dimension in inches to avoid zero-division / negative-extent bugs
_MIN_EXTENT = 0.05

def _color_to_hex(color_obj) -> Optional[str]:
    if color_obj is None:
        return None
    try:
        if hasattr(color_obj, "rgb") and color_obj.rgb is not None:
            return f"#{str(color_obj.rgb).upper()}"
    except Exception:
        pass
    return None

class SlideDecompiler:
    def __init__(self, pptx_path: str):
        self.prs = pptx.Presentation(pptx_path)
        self.slide_width = self.prs.slide_width.inches if self.prs.slide_width else 13.333
        self.slide_height = self.prs.slide_height.inches if self.prs.slide_height else 7.5

    @staticmethod
    def _iter_shapes(
        shapes, parent_left: float = 0.0, parent_top: float = 0.0
    ) -> Generator[Tuple[Any, float, float], None, None]:
        """Yield (shape, offset_left, offset_top) recursively descending groups.
        Enterprise decks heavily nest elements inside GroupShapes; a flat
        iteration over slide.shapes silently drops those children.
        """
        for shape in shapes:
            if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP or hasattr(shape, "shapes"):
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
                if slide.background and slide.background.fill:
                    if slide.background.fill.type == 6:  # PICTURE
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

            archetype_name = "Multi-Card Content"
            if SlideGraphClassifier:
                try:
                    archetype = SlideGraphClassifier.classify(slide, index, len(self.prs.slides))
                    archetype_name = archetype.value
                except Exception:
                    pass

            slide_ast = {
                "slide_id": index + 1,
                "archetype": archetype_name,
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
        try:
            left = max(0.0, round((shape.left.inches if shape.left else 0.5) + offset_left, 3))
            top = max(0.0, round((shape.top.inches if shape.top else 0.5) + offset_top, 3))
            width = max(_MIN_EXTENT, round(shape.width.inches if shape.width else 2.0, 3))
            height = max(_MIN_EXTENT, round(shape.height.inches if shape.height else 1.0, 3))
        except Exception:
            left, top, width, height = 0.5, 0.5, 2.0, 1.0

        shape_id = getattr(shape, "shape_id", 0)
        shape_type = getattr(shape, "shape_type", None)

        shape_name_str = getattr(shape, "name", "") or ""
        base_data: Dict[str, Any] = {
            "id": shape_id,
            "name": shape_name_str,
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

        # Fill and Line properties
        fill_hex = None
        try:
            if shape.fill and shape.fill.type == MSO_FILL.SOLID and hasattr(shape.fill, "fore_color"):
                fill_hex = _color_to_hex(shape.fill.fore_color)
        except Exception:
            pass
        if fill_hex:
            base_data["fill_hex"] = fill_hex
            base_data["fill_color"] = fill_hex

        line_hex = None
        try:
            if shape.line and hasattr(shape.line, "color") and hasattr(shape.line.color, "rgb"):
                line_hex = _color_to_hex(shape.line.color)
        except Exception:
            pass
        if line_hex:
            base_data["line_hex"] = line_hex
            base_data["line_color"] = line_hex

        # Check for bottom frame
        if "BrandMorphBottomFrame" in shape_name_str or "BrandMorphAccentLine" in shape_name_str:
            base_data["type"] = "RECTANGLE_SHAPE"
            base_data["shape_name"] = "BrandMorphBottomFrame"
            return base_data

        # 1. Check for Picture / Image FIRST (so picture placeholders are not swallowed by has_text_frame)
        is_picture = False
        image_bytes = None
        content_type = "image/png"
        try:
            if shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
                if getattr(shape, "image", None) is not None:
                    is_picture = True
                    image_bytes = shape.image.blob
                    content_type = getattr(shape.image, "content_type", None) or f"image/{getattr(shape.image, 'ext', 'png')}"
        except Exception:
            pass

        if not is_picture:
            try:
                # Check for picture placeholder or blip in shape element
                blips = shape.element.xpath('.//a:blip')
                if blips:
                    r_id = blips[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if r_id and hasattr(shape, "part") and r_id in shape.part.related_parts:
                        rel = shape.part.related_parts[r_id]
                        if hasattr(rel, "blob"):
                            image_bytes = rel.blob
                            content_type = getattr(rel, "content_type", "image/png")
                            is_picture = True
            except Exception:
                pass

        if is_picture and image_bytes:
            try:
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                data_uri = f"data:{content_type};base64,{image_base64}"
                base_data["type"] = "PICTURE"
                base_data["image_data_uri"] = data_uri
                base_data["image_src"] = data_uri
                base_data["image_data"] = data_uri
                base_data["image_data_uri"] = data_uri
                return base_data
            except Exception:
                pass

        # 2. Text Container Frame
        if getattr(shape, "has_text_frame", False) and shape.text_frame and shape.text_frame.text.strip():
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

                runs_data = []
                for r in p.runs:
                    r_color = None
                    try:
                        if r.font and r.font.color and r.font.color.type is not None:
                            r_color = _color_to_hex(r.font.color)
                    except Exception:
                        pass
                    runs_data.append({
                        "text": r.text,
                        "font_name": r.font.name if r.font else None,
                        "font_size": r.font.size.pt if r.font and r.font.size else None,
                        "bold": bool(r.font.bold) if r.font else False,
                        "italic": bool(r.font.italic) if r.font else False,
                        "color": r_color,
                    })

                p_align = 'LEFT'
                try:
                    if str(p.alignment) == 'CENTER (2)':
                        p_align = 'CENTER'
                    elif str(p.alignment) == 'RIGHT (3)':
                        p_align = 'RIGHT'
                    elif str(p.alignment) == 'JUSTIFY (4)':
                        p_align = 'JUSTIFY'
                except Exception:
                    pass

                font_color = "#FFB81C" if is_title_frame else "#FFFFFF"
                font_name = "Times New Roman" if is_title_frame else "Arial"
                font_size = p.font.size.pt if p.font and p.font.size else (28.0 if is_title_frame else 12.0)

                paragraphs.append({
                    "text": p.text,
                    "level": getattr(p, "level", 0),
                    "font_size": font_size,
                    "font_face": font_name,
                    "font_color": font_color,
                    "bold": False if is_title_frame else (bool(p.font.bold) if p.font else False),
                    "italic": bool(p.font.italic) if p.font else False,
                    "underline": bool(p.font.underline) if p.font else False,
                    "align": p_align,
                    "runs": runs_data
                })

            base_data["type"] = "TEXT_CONTAINER"
            base_data["paragraphs"] = paragraphs
            base_data["is_title"] = is_title_frame
            return base_data

        # 3. Geometric Shapes / Arrows / Containers
        if shape_type in (MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.FREEFORM):
            shape_enum_str = str(getattr(shape, 'auto_shape_type', 'RECTANGLE'))
            if "ARROW" in shape_enum_str or "CHEVRON" in shape_enum_str:
                base_data["type"] = "ARROW_SHAPE"
            elif "OVAL" in shape_enum_str or "CIRCLE" in shape_enum_str:
                base_data["type"] = "OVAL_SHAPE"
            else:
                base_data["type"] = "RECTANGLE_SHAPE"

            base_data["shape_name"] = shape_enum_str
            return base_data

        # 4. Lines and Connectors
        tag = getattr(shape, "_element", None)
        is_connector = tag is not None and getattr(tag, "tag", "").endswith("}cxnSp")
        if shape_type == MSO_SHAPE_TYPE.LINE or is_connector:
            base_data["type"] = "LINE_SHAPE"
            base_data["shape_name"] = "CONNECTOR_LINE" if is_connector else "LINE"
            return base_data

        # 5. Tables
        is_table = shape_type == MSO_SHAPE_TYPE.TABLE or getattr(shape, "has_table", False)
        if is_table:
            base_data["type"] = "TABLE"
            base_data["shape_name"] = "TABLE_SHAPE"
            return base_data

        # 6. Charts
        is_chart = shape_type == MSO_SHAPE_TYPE.CHART or getattr(shape, "has_chart", False)
        if is_chart:
            base_data["type"] = "CHART"
            base_data["shape_name"] = "CHART_SHAPE"
            return base_data

        return None
