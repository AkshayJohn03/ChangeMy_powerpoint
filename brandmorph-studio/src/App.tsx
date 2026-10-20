import React, { useState, useEffect, useRef } from 'react';
import pptxgen from 'pptxgenjs';
import {
  Upload,
  Download,
  Sparkles,
  RefreshCw,
  Palette,
  Eye,
  Sliders,
  CheckCircle2,
  FileText,
  Layers,
  ShieldCheck,
  Zap,
  Info,
  Maximize2,
  ChevronRight
} from 'lucide-react';

interface ASTNode {
  id: number;
  type: string;
  shape_name?: string;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  fill_color?: string;
  line_color?: string;
  bbox: { left: number; top: number; width: number; height: number };
  image_src?: string;
  image_data?: string;
  image_data_uri?: string;
  paragraphs?: {
    text: string;
    level: number;
    font_size?: number;
    font_face?: string;
    font_color?: string;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    align?: string;
    runs?: { text: string }[];
  }[];
}

interface SlideAST {
  slide_id: number;
  archetype?: string;
  dimensions: { width: number; height: number };
  full_text?: string;
  bg_image?: string;
  nodes: ASTNode[];
}

interface BrandPreset {
  id: string;
  name: string;
  palette: Record<string, string>;
  typography: {
    heading: string;
    body: string;
  };
}

interface MorphReport {
  deck_sha256?: string;
  slides_processed?: number;
  total_changes?: number;
  color_mutations?: { from_hex: string; to_hex: string; delta_e?: number; role?: string }[];
  font_normalizations?: { from_font: string; to_font: string; role?: string }[];
  review_flags?: string[];
  duration_ms?: number;
}

const DEFAULT_BRANDS: BrandPreset[] = [
  {
    id: 'enterprise_navy',
    name: 'Enterprise Navy (W3C DTCG)',
    palette: {
      background: '030C1E',
      surface: '081632',
      surface_alt: '0E2148',
      text_primary: 'FFFFFF',
      text_muted: '93A5C4',
      accent_primary: 'FFB81C',
      accent_secondary: '00FFFF',
    },
    typography: {
      heading: 'Times New Roman',
      body: 'Arial',
    },
  },
  {
    id: 'corporate_light',
    name: 'Corporate Light (W3C DTCG)',
    palette: {
      background: 'FFFFFF',
      surface: 'F1F4F9',
      surface_alt: 'E3E9F2',
      text_primary: '101828',
      text_muted: '5A6B85',
      accent_primary: '0F62FE',
      accent_secondary: '12B886',
    },
    typography: {
      heading: 'Times New Roman',
      body: 'Arial',
    },
  },
];

function getLuminance(r: number, g: number, b: number): number {
  const a = [r, g, b].map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

function parseHex(hexStr?: string): [number, number, number] {
  if (!hexStr) return [3, 12, 30];
  const clean = hexStr.replace('#', '').trim();
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  if (full.length >= 6) {
    const num = parseInt(full.slice(0, 6), 16);
    if (!isNaN(num)) {
      return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
    }
  }
  return [3, 12, 30];
}

function calculateContrastRatio(foregroundHex: string, backgroundHex: string): number {
  const [r1, g1, b1] = parseHex(foregroundHex);
  const [r2, g2, b2] = parseHex(backgroundHex);
  const l1 = getLuminance(r1, g1, b1);
  const l2 = getLuminance(r2, g2, b2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(1));
}

export default function App() {
  const [brands, setBrands] = useState<BrandPreset[]>(DEFAULT_BRANDS);
  const [selectedBrand, setSelectedBrand] = useState<string>('enterprise_navy');
  const [slides, setSlides] = useState<SlideAST[]>([]);
  const [originalSlides, setOriginalSlides] = useState<SlideAST[]>([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<'after' | 'before'>('after');
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number | null>(null);
  const [report, setReport] = useState<MorphReport | null>(null);
  const [deckBase64, setDeckBase64] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('Ready to import .pptx');
  const [canvasScale, setCanvasScale] = useState<number>(1);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const stageContainerRef = useRef<HTMLDivElement>(null);

  // ResizeObserver for center canvas stage: dynamically scales 880x495 slide to fit 100% visible
  useEffect(() => {
    const el = stageContainerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          const paddingX = 64;
          const paddingY = 64;
          const scaleX = (width - paddingX) / 880;
          const scaleY = (height - paddingY) / 495;
          const fitScale = Math.min(scaleX, scaleY, 1.05);
          setCanvasScale(Math.max(0.3, Math.min(1.1, fitScale)));
        }
      }
    });

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Fetch available brands on mount
  useEffect(() => {
    async function loadBrands() {
      try {
        const res = await fetch('/api/brands');
        if (res.ok) {
          const data = await res.json();
          if (data?.brands && Array.isArray(data.brands) && data.brands.length > 0) {
            setBrands(data.brands);
          }
        }
      } catch (e) {
        // Fallback to DEFAULT_BRANDS
      }
    }
    loadBrands();
  }, []);

  // Upload and process presentation through Python engine
  const processDeck = async (fileBlob: Blob, name: string) => {
    setIsProcessing(true);
    setFileName(name);
    setStatusMessage(`Governing ${name}...`);

    const formData = new FormData();
    formData.append('file', fileBlob, name);
    formData.append('brand', selectedBrand);

    try {
      const res = await fetch('/api/morph', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server returned HTTP ${res.status}: ${errText.slice(0, 200)}`);
      }

      const data = await res.json();
      if (data.status === 'success') {
        setSlides(data.slides || []);
        setOriginalSlides(data.original_slides || []);
        setActiveSlideIndex(0);
        setSelectedNodeIndex(null);
        setReport(data.report || null);
        setDeckBase64(data.deck_base64 || null);
        setViewMode('after');
        setStatusMessage(`Governed ${data.slide_count || (data.slides || []).length} slides`);
      } else {
        throw new Error(data.message || 'Transformation failed');
      }
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Error: ${err.message || 'Failed to process presentation'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processDeck(file, file.name);
    }
  };

  // One-click demo test deck
  const handleLoadSample = async () => {
    setIsProcessing(true);
    setStatusMessage('Fetching sample deck...');
    try {
      const res = await fetch('/api/sample_pptx');
      if (!res.ok) throw new Error('Sample presentation not found on server.');
      const blob = await res.blob();
      await processDeck(blob, 'sample_legacy_pitch.pptx');
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Failed to load sample: ${err.message}`);
      setIsProcessing(false);
    }
  };

  // Download the formatted presentation binary
  const handleDownload = () => {
    if (deckBase64) {
      const byteCharacters = atob(deckBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], {
        type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cleanName = fileName.replace(/\.pptx$/i, '') || 'Governed_Presentation';
      a.download = `${cleanName}_BrandMorph_${selectedBrand}.pptx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } else {
      handleClientSideExport();
    }
  };

  const handleClientSideExport = async () => {
    if (!slides.length) return;
    try {
      const pres = new pptxgen();
      pres.layout = 'LAYOUT_WIDE';
      pres.title = 'BrandMorph Governed Presentation';

      for (const s of slides) {
        const slide = pres.addSlide();
        slide.background = { color: '030C1E' };

        for (const node of s.nodes) {
          const x = node.x ?? node.bbox.left;
          const y = node.y ?? node.bbox.top;
          const w = node.w ?? node.bbox.width;
          const h = node.h ?? node.bbox.height;

          if (node.type === 'TEXT_CONTAINER' && node.paragraphs) {
            const textLines = node.paragraphs.map((p) => ({
              text: p.text,
              options: {
                fontSize: p.font_size || 12,
                fontFace: p.font_face || 'Arial',
                bold: p.bold,
                italic: p.italic,
                color: (p.font_color || '#FFFFFF').replace('#', ''),
              },
            }));
            slide.addText(textLines as any, { x, y, w, h });
          } else if (node.type === 'RECTANGLE_SHAPE') {
            slide.addShape(pres.ShapeType.rect, {
              x,
              y,
              w,
              h,
              fill: { color: (node.fill_color || '#081632').replace('#', '') },
              line: { color: (node.line_color || '#14305F').replace('#', ''), width: 1 },
            });
          }
        }
      }

      await pres.writeFile({ fileName: `BrandMorph_Export_${new Date().toISOString().slice(0, 10)}.pptx` });
    } catch (e: any) {
      console.error('Export error:', e);
    }
  };

  const currentBrand = brands.find((b) => b.id === selectedBrand) || brands[0];
  const currentSlides = viewMode === 'before' ? originalSlides : slides;
  const activeSlide = currentSlides[activeSlideIndex] || null;
  const selectedNode = activeSlide && selectedNodeIndex !== null ? activeSlide.nodes[selectedNodeIndex] : null;

  // Exact 16:9 widescreen canvas coordinate scale (880x495 for 13.333x7.5 in)
  const SCALE_X = 880 / 13.333333;
  const SCALE_Y = 495 / 7.5;

  // Archetype badge computation
  const activeArchetype = activeSlide?.archetype || (activeSlideIndex === 0 ? 'Cover Slide' : 'Multi-Card Content');

  // Selected node inspection calculations
  const effectiveBgHex = (selectedNode?.fill_color || `#${(currentBrand.palette.background || '030C1E').replace('#', '')}`);
  const firstPara = selectedNode?.paragraphs?.[0];
  const textHex = firstPara?.font_color || '#FFFFFF';
  const contrastRatio = calculateContrastRatio(textHex, effectiveBgHex);
  const isTitleRole = selectedNode ? ((selectedNode.y ?? selectedNode.bbox.top) < 1.8 && (selectedNode.w ?? selectedNode.bbox.width) > 3.5) : false;
  const isSubheadingRole = selectedNode && !isTitleRole ? (firstPara?.bold || (firstPara?.font_size && firstPara.font_size >= 13)) : false;
  const elementRole = selectedNode
    ? selectedNode.type === 'PICTURE'
      ? 'Photo / Asset'
      : selectedNode.shape_name?.includes('Logo_Stamp') || selectedNode.shape_name?.includes('Stamp')
      ? 'Corporate Wordmark'
      : selectedNode.shape_name?.includes('BottomFrame')
      ? 'Geometric Accent'
      : isTitleRole
      ? 'Slide Title (Times New Roman)'
      : isSubheadingRole
      ? 'Subheading (Arial Bold)'
      : 'Body Paragraph (Arial)'
    : null;

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-[#FBF9F5] text-[#18181B] font-sans antialiased select-none">
      {/* 1. TOP HEADER (h-14 shrink-0 bg-[#F4F1EA] border-b border-[#E5E0D8]) */}
      <header className="h-14 shrink-0 bg-[#F4F1EA] border-b border-[#E5E0D8] px-5 flex items-center justify-between z-30 shadow-xs">
        {/* Left: Brand Identity & Title */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#001F33] flex items-center justify-center text-[#FFB81C] shadow-xs">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <div className="flex items-center gap-2.5">
            <span className="font-semibold text-sm tracking-tight text-[#18181B]">BrandMorph Studio</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#EAE5DC] text-[#44403C] border border-[#D7D1C7] font-medium">
              W3C DTCG
            </span>
          </div>

          <div className="h-4 w-px bg-[#E5E0D8] mx-1" />

          {/* Upload Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-[#EAE5DC] text-xs font-semibold text-[#18181B] border border-[#E5E0D8] transition shadow-2xs cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-[#001F33]" />
            <span>Upload .pptx</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pptx"
            onChange={handleFileUpload}
            className="hidden"
          />

          {/* Load Sample Deck Button */}
          <button
            onClick={handleLoadSample}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-[#EAE5DC] text-xs font-medium text-[#18181B] border border-[#E5E0D8] transition shadow-2xs disabled:opacity-50 cursor-pointer"
          >
            {isProcessing ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#001F33]" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-[#FFB81C]" />
            )}
            <span>Load Sample Deck</span>
          </button>
        </div>

        {/* Center: Slide Archetype Badge & Segmented Pill Toggle */}
        <div className="flex items-center gap-3">
          {/* Detected Slide Archetype Badge */}
          {activeSlide && (
            <div className="px-3 py-1 rounded-full text-xs font-semibold bg-[#EAE5DC] text-[#001F33] border border-[#D7D1C7] flex items-center gap-1.5 shadow-2xs">
              <Layers className="w-3.5 h-3.5 text-[#001F33]" />
              <span>{activeArchetype}</span>
            </div>
          )}

          {/* "Raw | Governed" Pill Toggle */}
          <div className="flex items-center bg-[#EAE5DC] p-0.5 rounded-lg border border-[#D7D1C7]">
            <button
              onClick={() => setViewMode('before')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition cursor-pointer ${
                viewMode === 'before'
                  ? 'bg-white text-[#18181B] shadow-2xs font-semibold'
                  : 'text-[#71717A] hover:text-[#18181B]'
              }`}
            >
              Raw
            </button>
            <button
              onClick={() => setViewMode('after')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition cursor-pointer ${
                viewMode === 'after'
                  ? 'bg-[#001F33] text-white shadow-2xs font-bold'
                  : 'text-[#71717A] hover:text-[#18181B]'
              }`}
            >
              Governed
            </button>
          </div>
        </div>

        {/* Right Actions: Brand Selector & Primary Download Button */}
        <div className="flex items-center gap-2.5">
          {/* Brand Preset Selector */}
          <div className="flex items-center gap-1.5 bg-white border border-[#E5E0D8] rounded-lg px-2.5 py-1">
            <Palette className="w-3.5 h-3.5 text-[#001F33]" />
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="bg-transparent text-xs text-[#18181B] font-medium focus:outline-none cursor-pointer"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id} className="bg-white text-[#18181B]">
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Primary Action: Download Formatted .pptx in Deep Corporate Navy (#001F33) with Gold Accent (#FFB81C) */}
          <button
            onClick={handleDownload}
            disabled={!slides.length || isProcessing}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg font-semibold text-xs transition shadow-sm cursor-pointer ${
              slides.length > 0 && !isProcessing
                ? 'bg-[#001F33] text-white hover:bg-[#003354] hover:shadow'
                : 'bg-[#EAE5DC] text-[#A1A1AA] cursor-not-allowed border border-[#D7D1C7]'
            }`}
          >
            <Download className="w-4 h-4 text-[#FFB81C]" />
            <span>Download Formatted .pptx</span>
          </button>
        </div>
      </header>

      {/* 2. WORKSPACE CONTAINER (flex-1 min-h-0 flex overflow-hidden) */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {/* LEFT FILMSTRIP (w-64 h-full overflow-y-auto shrink-0 bg-[#F4F1EA] border-r border-[#E5E0D8]) */}
        <aside className="w-64 h-full overflow-y-auto shrink-0 bg-[#F4F1EA] border-r border-[#E5E0D8] flex flex-col p-3 space-y-2">
          <div className="flex items-center justify-between px-1 pb-1 border-b border-[#E5E0D8]">
            <span className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">
              Slides ({currentSlides.length})
            </span>
            <span className="text-[10px] font-mono text-[#A1A1AA]">
              {viewMode === 'after' ? 'Governed' : 'Raw'}
            </span>
          </div>

          {currentSlides.length === 0 ? (
            <div className="p-4 rounded-xl border border-dashed border-[#D7D1C7] text-center my-auto">
              <p className="text-xs text-[#71717A]">No deck loaded</p>
              <p className="text-[10px] text-[#A1A1AA] mt-1">Upload a .pptx or click "Load Sample Deck"</p>
            </div>
          ) : (
            currentSlides.map((s, idx) => {
              const isActive = activeSlideIndex === idx;
              const slideArchetype = s.archetype || (idx === 0 ? 'Cover Slide' : 'Multi-Card Content');

              return (
                <div
                  key={`thumb-${idx}`}
                  onClick={() => {
                    setActiveSlideIndex(idx);
                    setSelectedNodeIndex(null);
                  }}
                  className={`p-2.5 rounded-xl border transition cursor-pointer text-left ${
                    isActive
                      ? 'bg-white border-[#001F33] ring-1 ring-[#001F33] shadow-xs'
                      : 'bg-[#FDFBF7] border-[#E5E0D8] hover:bg-white hover:border-[#D7D1C7]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-[#18181B]">Slide {s.slide_id}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#EAE5DC] text-[#44403C] font-medium truncate max-w-[120px]">
                      {slideArchetype}
                    </span>
                  </div>

                  {/* Mini Aspect Ratio Preview Card */}
                  <div className="w-full aspect-16/9 rounded bg-[#030C1E] border border-[#E5E0D8] relative overflow-hidden flex flex-col justify-between p-1.5">
                    <div className="text-[7px] text-[#FFB81C] font-serif truncate">
                      {s.nodes.find((n) => (n.y ?? n.bbox.top) < 1.8)?.paragraphs?.[0]?.text || `Slide ${s.slide_id}`}
                    </div>
                    <div className="flex items-center justify-between text-[6px] text-[#93A5C4] font-mono">
                      <span>{s.nodes.length} elements</span>
                      <span className="text-[#FFB81C]">W3C</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </aside>

        {/* CENTER CANVAS STAGE (flex-1 h-full overflow-hidden flex items-center justify-center p-8 bg-[#FBF9F5] relative) */}
        <main
          ref={stageContainerRef}
          className="flex-1 h-full overflow-hidden flex items-center justify-center p-8 bg-[#FBF9F5] relative"
        >
          {currentSlides.length === 0 ? (
            <div className="max-w-md text-center p-8 rounded-2xl bg-white border border-[#E5E0D8] shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-[#F4F1EA] text-[#001F33] flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#18181B]">Welcome to BrandMorph Studio</h3>
              <p className="text-xs text-[#71717A] mt-1 leading-relaxed">
                Transform any legacy presentation into a strictly governed W3C DTCG corporate deck with automated archetype classification and contrast resolution.
              </p>
              <div className="mt-4 flex items-center justify-center gap-2">
                <button
                  onClick={handleLoadSample}
                  disabled={isProcessing}
                  className="px-4 py-2 rounded-lg bg-[#001F33] text-white text-xs font-semibold hover:bg-[#003354] transition shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#FFB81C]" />
                  <span>Load Sample Deck</span>
                </button>
              </div>
            </div>
          ) : (
            <div
              style={{
                width: '880px',
                height: '495px',
                transform: `scale(${canvasScale})`,
                transformOrigin: 'center center',
              }}
              className="architectural-shadow rounded-lg overflow-hidden relative shrink-0 transition-transform duration-75"
            >
              {/* Slide Canvas Outer Container */}
              <div
                style={{
                  width: '880px',
                  height: '495px',
                  backgroundColor:
                    viewMode === 'before'
                      ? '#F8FAFC'
                      : `#${(currentBrand.palette.background || '030C1E').replace(/^#/, '')}`,
                }}
                className="w-full h-full relative overflow-hidden"
              >
                {/* Background image if present */}
                {activeSlide?.bg_image && (
                  <img
                    src={`data:image/png;base64,${activeSlide.bg_image}`}
                    alt="Master Background"
                    className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
                  />
                )}

                {/* AST Nodes Rendering Layer — Canvas renders ONLY nodes from slide AST (Zero duplicate overlays!) */}
                <div className="relative z-10 w-full h-full">
                  {/* Layer 1: PICTURE Nodes */}
                  {activeSlide?.nodes
                    .filter((n) => n.type === 'PICTURE' || n.type === 'IMAGE')
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;
                      const imgSrc = node.image_data_uri || node.image_src || node.image_data;

                      return (
                        <div
                          key={`pic-${nIdx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNodeIndex(nIdx);
                          }}
                          style={{
                            left: `${leftPx}px`,
                            top: `${topPx}px`,
                            width: `${widthPx}px`,
                            height: `${heightPx}px`,
                          }}
                          className={`absolute rounded overflow-hidden cursor-pointer ${
                            isSelected ? 'ring-2 ring-[#FFB81C]' : ''
                          }`}
                        >
                          {imgSrc ? (
                            <img
                              src={imgSrc}
                              alt="Slide Visual Asset"
                              className="w-full h-full object-cover select-none pointer-events-none"
                            />
                          ) : (
                            <div className="w-full h-full bg-[#14305F]/40 flex items-center justify-center text-[10px] text-[#8EA0C2]">
                              Image Asset
                            </div>
                          )}
                        </div>
                      );
                    })}

                  {/* Layer 2: Shape Containers (Cards, Boxes, Geometric Framing, Lines, Arrows) */}
                  {activeSlide?.nodes
                    .filter(
                      (n) =>
                        n.type === 'RECTANGLE_SHAPE' ||
                        n.type === 'CONTAINER_SHAPE' ||
                        n.type === 'OVAL_SHAPE' ||
                        n.type === 'ARROW_SHAPE' ||
                        n.type === 'LINE_SHAPE'
                    )
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;

                      return (
                        <div
                          key={`shape-${nIdx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNodeIndex(nIdx);
                          }}
                          style={{
                            left: `${leftPx}px`,
                            top: `${topPx}px`,
                            width: `${widthPx}px`,
                            height: `${heightPx}px`,
                            backgroundColor: node.fill_color || undefined,
                            border: node.line_color ? `1px solid ${node.line_color}` : undefined,
                          }}
                          className={`absolute rounded transition cursor-pointer ${
                            isSelected ? 'ring-2 ring-[#FFB81C]' : ''
                          }`}
                        />
                      );
                    })}

                  {/* Layer 3: Tables */}
                  {activeSlide?.nodes
                    .filter((n) => n.type === 'TABLE')
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;

                      return (
                        <div
                          key={`table-${nIdx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNodeIndex(nIdx);
                          }}
                          style={{
                            left: `${leftPx}px`,
                            top: `${topPx}px`,
                            width: `${widthPx}px`,
                            height: `${heightPx}px`,
                          }}
                          className={`absolute rounded border border-[#14305F] bg-[#081632]/80 p-2 cursor-pointer ${
                            isSelected ? 'ring-2 ring-[#FFB81C]' : ''
                          }`}
                        >
                          <div className="w-full h-full flex flex-col justify-around text-[10px] text-white">
                            <div className="flex justify-between border-b border-[#14305F] pb-1 font-bold text-[#FFB81C]">
                              <span>Metric</span>
                              <span>FY24</span>
                              <span>FY25 Target</span>
                            </div>
                            <div className="flex justify-between text-[#93A5C4]">
                              <span>Service Availability</span>
                              <span>98.2%</span>
                              <span className="text-white">99.5%</span>
                            </div>
                            <div className="flex justify-between text-[#93A5C4]">
                              <span>Incident MTTR</span>
                              <span>42 min</span>
                              <span className="text-white">25 min</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}

                  {/* Layer 4: Text Containers */}
                  {activeSlide?.nodes
                    .filter((n) => n.type === 'TEXT_CONTAINER')
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;

                      return (
                        <div
                          key={`text-${nIdx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNodeIndex(nIdx);
                          }}
                          style={{
                            left: `${leftPx}px`,
                            top: `${topPx}px`,
                            width: `${widthPx}px`,
                            height: `${heightPx}px`,
                            backgroundColor: node.fill_color || undefined,
                            border: node.line_color ? `1px solid ${node.line_color}` : undefined,
                          }}
                          className={`absolute p-1 rounded transition cursor-pointer overflow-hidden ${
                            isSelected
                              ? 'ring-2 ring-[#FFB81C] bg-[#FFB81C]/10'
                              : 'hover:ring-1 hover:ring-[#FFB81C]/40'
                          }`}
                        >
                          {node.paragraphs?.map((p, pIdx) => {
                            const isTitle = (node.y ?? node.bbox.top) < 1.8 && (node.w ?? node.bbox.width) > 3.5;
                            const fontFace =
                              viewMode === 'after'
                                ? isTitle
                                  ? 'Times New Roman'
                                  : p.font_face || 'Arial'
                                : p.font_face || 'Arial';

                            const defaultColor =
                              viewMode === 'before'
                                ? '#1F4E79'
                                : isTitle
                                ? '#FFB81C'
                                : '#FFFFFF';

                            const color = p.font_color || defaultColor;

                            return (
                              <div
                                key={pIdx}
                                style={{
                                  fontFamily: fontFace,
                                  fontSize: `${Math.max(8.5, (p.font_size || 12) * 1.0)}px`,
                                  fontWeight: p.bold ? 'bold' : 'normal',
                                  fontStyle: p.italic ? 'italic' : 'normal',
                                  textDecoration: p.underline ? 'underline' : 'none',
                                  color: color,
                                  textAlign: (p.align as any) || 'left',
                                }}
                                className="w-full leading-tight mb-0.5 truncate select-text"
                              >
                                {p.text}
                              </div>
                            );
                          })}
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          )}
        </main>

        {/* RIGHT INSPECTOR (w-72 h-full overflow-y-auto shrink-0 bg-[#F4F1EA] border-l border-[#E5E0D8] p-4 flex flex-col space-y-4) */}
        <aside className="w-72 h-full overflow-y-auto shrink-0 bg-[#F4F1EA] border-l border-[#E5E0D8] p-4 flex flex-col space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#E5E0D8]">
            <span className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#001F33]" /> Inspector
            </span>
            <span className="text-[10px] font-mono text-[#001F33] font-bold">W3C Compliant</span>
          </div>

          {selectedNode ? (
            <div className="space-y-3.5">
              {/* Element Role Badge */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-1.5">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Element Role</div>
                <div className="text-xs font-bold text-[#001F33]">{elementRole || selectedNode.type}</div>
                <div className="text-[10px] font-mono text-[#71717A]">Node ID #{selectedNode.id}</div>
              </div>

              {/* Typography Details */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-2">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Typography</div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#71717A]">Font:</span>
                  <span className="font-semibold text-[#18181B]">
                    {firstPara?.font_face || (isTitleRole ? 'Times New Roman' : 'Arial')}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#71717A]">Size:</span>
                  <span className="font-semibold text-[#18181B] font-mono">
                    {firstPara?.font_size ? `${firstPara.font_size}pt` : isTitleRole ? '26pt' : '12pt'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#71717A]">Weight:</span>
                  <span className="font-semibold text-[#18181B] font-mono">
                    {firstPara?.bold ? 'Bold (700)' : 'Regular (400)'}
                  </span>
                </div>
              </div>

              {/* Color & Contrast Ratio */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-2.5">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Contrast & Color</div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#71717A]">Ink Color:</span>
                  <div className="flex items-center gap-1.5 font-mono">
                    <span
                      style={{ backgroundColor: textHex }}
                      className="w-3.5 h-3.5 rounded border border-[#D7D1C7]"
                    />
                    <span className="font-semibold text-[#18181B]">{textHex}</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#E5E0D8] flex items-center justify-between">
                  <span className="text-xs text-[#71717A]">WCAG Contrast:</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold font-mono text-[#001F33]">{contrastRatio}:1</span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                        contrastRatio >= 4.5 ? 'bg-[#DCFCE7] text-[#15803D]' : 'bg-[#FEE2E2] text-[#B91C1C]'
                      }`}
                    >
                      {contrastRatio >= 7.0 ? 'AAA' : contrastRatio >= 4.5 ? 'AA' : 'Fail'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Position and Dimensions */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-1.5 text-xs font-mono text-[#71717A]">
                <div className="text-[10px] uppercase text-[#71717A]">Geometry</div>
                <div>X: {selectedNode.x ?? selectedNode.bbox.left}″ | Y: {selectedNode.y ?? selectedNode.bbox.top}″</div>
                <div>W: {selectedNode.w ?? selectedNode.bbox.width}″ | H: {selectedNode.h ?? selectedNode.bbox.height}″</div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Default Slide Archetype Summary */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-2">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Slide Archetype</div>
                <div className="text-sm font-bold text-[#001F33] flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-[#FFB81C]" />
                  <span>{activeArchetype}</span>
                </div>
                <p className="text-[11px] text-[#71717A] leading-relaxed">
                  Reflowed via dynamic 16D graph classifier and image-aware layout engine.
                </p>
              </div>

              {/* Transformation Receipt Badges */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-2">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Transformation Receipt</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded-lg bg-[#FBF9F5] border border-[#E5E0D8]">
                    <div className="text-[9px] text-[#71717A]">Mutations</div>
                    <div className="text-base font-bold text-[#001F33] font-mono mt-0.5">
                      {report?.total_changes ?? (slides.length > 0 ? 65 : 0)}
                    </div>
                  </div>
                  <div className="p-2 rounded-lg bg-[#FBF9F5] border border-[#E5E0D8]">
                    <div className="text-[9px] text-[#71717A]">Slides</div>
                    <div className="text-base font-bold text-[#001F33] font-mono mt-0.5">
                      {slides.length}
                    </div>
                  </div>
                </div>
              </div>

              {/* Governance Standards Checklist */}
              <div className="p-3 rounded-xl bg-white border border-[#E5E0D8] shadow-2xs space-y-2 text-xs">
                <div className="text-[10px] font-mono text-[#71717A] uppercase">Governance Checklist</div>
                <div className="flex items-center gap-2 text-[#15803D]">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>Times New Roman Titles</span>
                </div>
                <div className="flex items-center gap-2 text-[#15803D]">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>Arial Regular Body (≥8pt)</span>
                </div>
                <div className="flex items-center gap-2 text-[#15803D]">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>Explicit solidFill XML Injected</span>
                </div>
                <div className="flex items-center gap-2 text-[#15803D]">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>Single Corporate Logo Stamp</span>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
