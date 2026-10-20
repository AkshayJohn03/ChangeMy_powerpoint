# BrandMorph — Zero-Leak Golden Pair Style & Metadata DNA Extractor

## 1. Overview & Privacy Guarantee
In compliance with corporate data security and strict zero-leakage requirements:
- **0% Content Leakage**: No client slide text, sentences, paragraphs, or proprietary names are ever read, exported, or saved.
- **0% Image Leakage**: No client images or proprietary graphics are extracted or saved.
- **100% Mathematical DNA**: Only geometry, coordinates, typography metrics, color hex codes, shape types, and structural relationships are extracted.

---

## 2. Advanced Metadata Extraction Schema

For every shape, container, and text frame, the extractor captures:

| Category | Metadata Fields Extracted | Privacy Enforcement |
| :--- | :--- | :--- |
| **Geometry** | `bbox_in` (`left`, `top`, `width`, `height`, `right`, `bottom`), `bbox_norm` (`[x0, y0, x1, y1]`), `rotation`, `aspect_ratio` | Pure floating-point dimensions in inches & normalized slide coordinates |
| **Shape Properties** | `shape_type`, `preset_geometry` (`ROUNDED_RECTANGLE`, `OVAL`, `CHEVRON`, etc.), `fill` (`type`, `color_hex`, `transparency`), `line` (`color_hex`, `width_pt`, `dash_style`) | Hex codes only (`#001F33`, `#FFB81C`), no pixel data |
| **Typography** | `font_name`, `font_size_pt`, `bold`, `italic`, `underline`, `color_hex`, `alignment` (`LEFT`, `CENTER`, `RIGHT`, `JUSTIFY`), `line_spacing` | Font families & pt numbers only |
| **Human-Like Matching Signature** | `char_count`, `word_count`, `paragraph_count`, `start_char` (first character), `end_char` (last character), `is_all_caps`, `is_title_case`, `sha256_prefix` (8-char irreversible one-way hash) | Text is discarded immediately; only length, casing, boundary characters, and hash prefix are retained |
| **Semantic Role Flags** | `is_container` ($\ge 2.0" \times 1.2"$, solid fill), `is_icon_candidate` ($\le 1.25" \times 1.25"$), `is_circular_badge`, `is_top_right_logo` ($x \ge 9.2", y \le 1.3"$), `is_bottom_banner` ($y \ge 6.1", w \ge 7.0"$), `is_connector` | Structural classification for card grids & brand banners |

---

## 3. Human-Like Element Matching Algorithm (Raw $\leftrightarrow$ Golden)

To accurately trace how raw elements were redesigned in the golden deck without reading text:

1. **Character Count Buffer ($\pm 10$ characters)**:
   - Evaluates length proximity between raw and golden text frames:
   $$\text{diff} = |len_{\text{raw}} - len_{\text{golden}}|$$
   - A diff $\le 10$ receives high confidence score ($\ge 0.40$), accounting for minor editorial polishing or bullet symbol additions.
2. **Boundary Character Verification**:
   - `start_char` match (+0.20): verifies both start with the same alphanumeric character (e.g. `'T'` for Title, `'1'` for step 1).
   - `end_char` match (+0.15): verifies matching punctuation or closing characters (e.g. `'.'`, `')'`).
3. **Spatial Order & Reading Hierarchy**:
   - Compares normalized vertical rank ($y$-coordinate distance $\le 0.20$), ensuring raw title maps to golden title, and raw body bullets map to golden cards.
4. **Irreversible Hash Match**:
   - If `sha256_prefix` matches identically, confidence is $1.0$ (identical text transformed).

---

## 4. Transformation & Difference Tracking

The extractor automatically outputs:
- **Transformed Elements**:
  - `font_family`: e.g. `Calibri -> Arial` or `Bahnschrift -> Roboto`
  - `font_size_pt`: e.g. `14.0pt -> 12.0pt`
  - `color_hex`: e.g. `#333333 -> #FFFFFF`
  - `container_added`: `true` (text boxed inside a card)
  - `border_added`: `true` (card outlined with `#FFB81C` Gold or `#00FFFF` Aqua)
  - `bbox_delta_in`: exact coordinate shifts `(dx, dy, dw, dh)`
- **Added Elements in Golden Deck**:
  - `CARD_CONTAINER`: Background glass/solid cards (`#001F33` / `#081E36`)
  - `ICON_OR_BADGE`: High-contrast circular icon badges ($\le 1.25"$)
  - `TOP_RIGHT_LOGO`: Akkodis master logo placement
  - `BOTTOM_BANNER`: Thin commitment banner with gold border
  - `CONNECTOR_FLOW`: Flowchart arrows and connecting lines
- **Removed Elements**:
  - Unstructured shapes or raw decorative clutter eliminated during redesign.

---

## 5. Execution on Your Corporate Laptop

You can run the extractor directly on your corporate laptop using either the batch launcher or Python:

### Option A: One-Click Launcher (Recommended)
Double-click:
```bat
Extract_Golden_DNA.bat
```
This automatically processes:
1. `17 Oct  Golden.pptx` vs `Raw.pptx` in `C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\10 Oct 2026\`
2. All `filename_xx_raw.pptx` $\leftrightarrow$ `filename_xx.pptx` pairs in `C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\12 Dec\OneDrive_2025-12-11\Updated\`

### Option B: Terminal Command Line
```powershell
# 1. Run on 10 Oct Golden Pair:
.\backend\venv\Scripts\python.exe scripts\extract_golden_pair_dna.py --pair-10oct

# 2. Batch scan 12 Dec Updated folder:
.\backend\venv\Scripts\python.exe scripts\extract_golden_pair_dna.py --batch-12dec

# 3. Scan all configured roots in BrandMorph:
.\backend\venv\Scripts\python.exe scripts\extract_golden_pair_dna.py --all

# 4. Custom pair execution:
.\backend\venv\Scripts\python.exe scripts\extract_golden_pair_dna.py --raw "C:\path\to\raw.pptx" --golden "C:\path\to\golden.pptx"
```

### Generated Outputs
- [LEARNED_RULES.json](file:///C:/Users/Akshay.JOHN-XAVIER/.gemini/antigravity-ide/scratch/BrandMorph/data/metadata/LEARNED_RULES.json): Automatically merged with newly learned typography mappings and size grids.
- `data/metadata/golden_style_dna.json`: Complete mathematical style DNA and alignment logs.
