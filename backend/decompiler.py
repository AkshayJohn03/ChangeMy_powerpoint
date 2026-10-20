import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.dml import MSO_FILL
from typing import Dict, List, Any, Optional
import base64

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

            for shape in slide.shapes:
                extracted = self._extract_shape_data(shape)
                if not extracted:
                    continue
                # If group returned list of flattened nodes
                items = extracted if isinstance(extracted, list) else [extracted]
                for node in items:
                    nodes.append(node)
                    if node.get("type") == "TEXT_CONTAINER" and node.get("paragraphs"):
                        for p in node["paragraphs"]:
                            if p.get("text"):
                                slide_text_accumulator.append(p["text"])

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

    def _extract_shape_data(self, shape) -> Any:
        try:
            left = shape.left.inches if shape.left is not None else 0.5
            top = shape.top.inches if shape.top is not None else 0.5
            width = shape.width.inches if shape.width is not None else 2.0
            height = shape.height.inches if shape.height is not None else 1.0
        except Exception:
            left, top, width, height = 0.5, 0.5, 2.0, 1.0

        shape_id = getattr(shape, "shape_id", 0)
        shape_type = getattr(shape, "shape_type", None)

        base_data = {
            "id": shape_id,
            "bbox": {
                "left": round(left, 3),
                "top": round(top, 3),
                "width": round(width, 3),
                "height": round(height, 3)
            }
        }

        # 0. Handle Grouped Shapes (Recursively flatten children with absolute positioning)
        if shape_type == MSO_SHAPE_TYPE.GROUP or hasattr(shape, "shapes"):
            flattened = []
            try:
                for sub in shape.shapes:
                    sub_res = self._extract_shape_data(sub)
                    if sub_res:
                        if isinstance(sub_res, list):
                            flattened.extend(sub_res)
                        else:
                            flattened.append(sub_res)
            except Exception:
                pass
            if flattened:
                return flattened

        # 1. Picture / Image Shape (Issue #6: Extract blob and data URI)
        if shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
            try:
                img = shape.image
                image_bytes = img.blob
                ext = getattr(img, "ext", "png").lower()
                if ext == "jpg":
                    ext = "jpeg"
                content_type = getattr(img, "content_type", f"image/{ext}")
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                data_uri = f"data:{content_type};base64,{image_base64}"
                base_data["type"] = "PICTURE"
                base_data["image_data_uri"] = data_uri
                base_data["image_data"] = data_uri
                return base_data
            except Exception:
                pass

        # Fill and Line properties
        fill_hex = None
        line_hex = None
        line_width = 1.0
        try:
            if shape.fill and shape.fill.type == MSO_FILL.SOLID:
                fill_hex = _color_to_hex(shape.fill.fore_color)
        except Exception:
            pass
        try:
            if shape.line and shape.line.fill and shape.line.fill.type == MSO_FILL.SOLID:
                line_hex = _color_to_hex(shape.line.color)
                if shape.line.width:
                    line_width = round(shape.line.width / 12700.0, 1)
        except Exception:
            pass

        base_data["fill_hex"] = fill_hex
        base_data["line_hex"] = line_hex
        base_data["line_width"] = line_width

        # 2. Text Container Frame
        if getattr(shape, "has_text_frame", False) and shape.text_frame and shape.text_frame.text.strip():
            paragraphs = []
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

                paragraphs.append({
                    "text": p.text,
                    "level": getattr(p, "level", 0),
                    "font_size": p.font.size.pt if p.font and p.font.size else 12,
                    "bold": bool(p.font.bold) if p.font else False,
                    "italic": bool(p.font.italic) if p.font else False,
                    "underline": bool(p.font.underline) if p.font else False,
                    "align": p_align,
                    "runs": runs_data
                })

            base_data["type"] = "TEXT_CONTAINER"
            base_data["paragraphs"] = paragraphs
            # Detect title heuristic
            is_title = (top < 1.6 and height < 1.8 and len(paragraphs) > 0) or ("title" in getattr(shape, "name", "").lower())
            base_data["is_title"] = is_title
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

        if hasattr(MSO_SHAPE_TYPE, "CONNECTOR") and shape_type == getattr(MSO_SHAPE_TYPE, "CONNECTOR"):
            base_data["type"] = "LINE_SHAPE"
            base_data["shape_name"] = "CONNECTOR_LINE"
            return base_data

        # 5. Tables
        if shape_type == MSO_SHAPE_TYPE.TABLE or hasattr(shape, "table"):
            base_data["type"] = "TABLE"
            return base_data

        # 6. Fallback connector tag check
        if tag is not None and getattr(tag, "tag", "").endswith("}cxnSp"):
            base_data["type"] = "LINE_SHAPE"
            base_data["shape_name"] = "CONNECTOR_LINE"
            return base_data

        return None
