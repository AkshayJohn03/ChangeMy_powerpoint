import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE
from typing import Dict, List, Any
import base64

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
                if slide.background and slide.background.fill and slide.background.fill.type == 6: # PICTURE
                    image_blob = slide.background.fill.picture.image.blob
                    bg_image_base64 = base64.b64encode(image_blob).decode('utf-8')
            except Exception:
                pass

            for shape in slide.shapes:
                node = self._extract_shape_data(shape)
                if node:
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

    def _extract_shape_data(self, shape) -> Dict[str, Any]:
        left = shape.left.inches if shape.left else 0.5
        top = shape.top.inches if shape.top else 0.5
        width = shape.width.inches if shape.width else 2.0
        height = shape.height.inches if shape.height else 1.0

        base_data = {
            "id": shape.shape_id,
            "bbox": {
                "left": round(left, 3),
                "top": round(top, 3),
                "width": round(width, 3),
                "height": round(height, 3)
            }
        }

        # 1. Text Container Frame
        if shape.has_text_frame:
            paragraphs = []
            for p in shape.text_frame.paragraphs:
                txt = p.text.strip()
                if "Font Guidance" in txt or "Do not change the template" in txt:
                    continue

                paragraphs.append({
                    "text": p.text,
                    "level": p.level,
                    "font_size": p.font.size.pt if p.font and p.font.size else 12,
                    "bold": p.font.bold if p.font else False,
                    "italic": p.font.italic if p.font else False,
                    "underline": p.font.underline if p.font else False,
                    "align": str(p.alignment) if p.alignment else 'LEFT',
                    "runs": [{"text": r.text} for r in p.runs]
                })
            base_data["type"] = "TEXT_CONTAINER"
            base_data["paragraphs"] = paragraphs
            return base_data

        # 2. Picture / Image Shape
        elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            try:
                image_bytes = shape.image.blob
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                base_data["type"] = "IMAGE"
                base_data["image_data"] = f"data:image/{shape.image.ext};base64,{image_base64}"
                return base_data
            except Exception:
                pass

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

        # 4. Lines and Connectors
        elif shape.shape_type in (MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.CONNECTOR):
            base_data["type"] = "LINE_SHAPE"
            base_data["shape_name"] = "CONNECTOR_LINE"
            return base_data

        return None
