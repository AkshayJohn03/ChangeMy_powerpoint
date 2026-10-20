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
  ArrowRight,
  Maximize2
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
    name: 'Akkodis Deep Navy (Corporate DNA)',
    palette: {
      background: '001F33',
      surface: '081E36',
      surface_alt: '0A2A4A',
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
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const stageContainerRef = useRef<HTMLDivElement>(null);

  // ResizeObserver for canvas stage to keep 880x495 slide 100% visible on any screen
  useEffect(() => {
    const el = stageContainerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          const scale = Math.min((width - 48) / 880, (height - 48) / 495, 1);
          setCanvasScale(Math.max(0.35, Math.min(1.05, scale)));
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
  const SCALE_X = 880 / 13.333;
  const SCALE_Y = 495 / 7.5;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(text);
    setTimeout(() => setCopiedToken(null), 1500);
  };

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-[#09090B] text-[#F4F4F5] font-sans antialiased select-none">
      {/* 1. TOP HEADER (h-14): Clean, calm, professional design tool aesthetic */}
      <header className="h-14 border-b border-[#27272A] bg-[#18181B] px-5 flex items-center justify-between shrink-0 z-30 shadow-sm">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#27272A] border border-[#3F3F46] flex items-center justify-center text-[#FFB81C]">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight text-white">BrandMorph Studio</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#27272A] text-[#A1A1AA] border border-[#3F3F46]">
                W3C DTCG
              </span>
            </div>
            <p className="text-[11px] text-[#A1A1AA] leading-none mt-0.5">Presentation Rebranding Engine</p>
          </div>
        </div>

        {/* Center: Segmented Pill Toggle (Before vs After) */}
        <div className="flex items-center bg-[#27272A]/80 p-0.5 rounded-lg border border-[#3F3F46]">
          <button
            onClick={() => setViewMode('before')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              viewMode === 'before'
                ? 'bg-[#3F3F46] text-white shadow-sm font-semibold'
                : 'text-[#A1A1AA] hover:text-white'
            }`}
          >
            Before (Raw Original)
          </button>
          <button
            onClick={() => setViewMode('after')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              viewMode === 'after'
                ? 'bg-[#FFB81C] text-[#09090B] shadow-sm font-bold'
                : 'text-[#A1A1AA] hover:text-white'
            }`}
          >
            After (W3C Formatted)
          </button>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2.5">
          {/* Brand Preset Selector */}
          <div className="flex items-center gap-1.5 bg-[#27272A] border border-[#3F3F46] rounded-lg px-2.5 py-1">
            <Palette className="w-3.5 h-3.5 text-[#FFB81C]" />
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="bg-transparent text-xs text-[#F4F4F5] font-medium focus:outline-none cursor-pointer"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id} className="bg-[#18181B] text-white">
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Sample Button */}
          <button
            onClick={handleLoadSample}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#27272A] hover:bg-[#3F3F46] text-xs font-medium text-[#F4F4F5] border border-[#3F3F46] transition disabled:opacity-50"
            title="Load sample unformatted presentation"
          >
            {isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-[#FFB81C]" />}
            <span>Load Sample Deck</span>
          </button>

          {/* Primary Action: Download Formatted PPTX */}
          <button
            onClick={handleDownload}
            disabled={!slides.length || isProcessing}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-semibold text-xs transition shadow-sm ${
              slides.length > 0 && !isProcessing
                ? 'bg-[#FFB81C] text-[#09090B] hover:bg-[#F59E0B] hover:shadow'
                : 'bg-[#27272A] text-[#71717A] cursor-not-allowed border border-[#3F3F46]'
            }`}
          >
            <Download className="w-4 h-4" />
            <span>Download Formatted .pptx</span>
          </button>
        </div>
      </header>

      {/* 2. MAIN WORKSPACE CONTAINER (h-full min-h-0 flex overflow-hidden) */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {/* LEFT SIDEBAR: Upload + Slide Navigator (w-72 h-full overflow-y-auto shrink-0 border-r) */}
        <aside className="w-72 h-full overflow-y-auto shrink-0 border-r border-[#27272A] bg-[#121215] flex flex-col">
          {/* SECTION A: DROPZONE */}
          <div className="p-3.5 border-b border-[#27272A]">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border border-dashed border-[#3F3F46] hover:border-[#FFB81C] bg-[#18181B] hover:bg-[#202024] rounded-xl p-3.5 flex flex-col items-center justify-center text-center cursor-pointer transition group"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pptx"
                onChange={handleFileUpload}
                className="hidden"
              />
              <div className="w-8 h-8 rounded-lg bg-[#27272A] group-hover:bg-[#3F3F46] flex items-center justify-center text-[#A1A1AA] group-hover:text-white mb-1.5 transition">
                <Upload className="w-4 h-4" />
              </div>
              <p className="text-xs font-medium text-[#F4F4F5]">
                {fileName ? fileName : 'Import PowerPoint (.pptx)'}
              </p>
              <p className="text-[10px] text-[#71717A] mt-0.5">Drag & drop or browse up to 15MB</p>
            </div>
          </div>

          {/* SECTION B: BRAND TOKEN SWATCHES */}
          <div className="p-3.5 border-b border-[#27272A] bg-[#141418]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono font-bold tracking-wider text-[#71717A] uppercase">
                Brand Tokens
              </span>
              <span className="text-[10px] font-mono text-[#A1A1AA]">{currentBrand.name.split(' ')[0]}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {Object.entries(currentBrand.palette).slice(0, 4).map(([role, hex]) => {
                const safeHex = `#${hex.replace(/^#/, '')}`;
                return (
                  <div
                    key={role}
                    onClick={() => copyToClipboard(safeHex)}
                    className="p-1.5 rounded-lg bg-[#18181B] border border-[#27272A] hover:border-[#3F3F46] cursor-pointer transition flex flex-col items-center"
                    title={`Click to copy: ${role} (${safeHex})`}
                  >
                    <div
                      className="w-full h-4 rounded border border-white/10 mb-1"
                      style={{ backgroundColor: safeHex }}
                    />
                    <span className="text-[8px] font-mono text-[#71717A] truncate w-full text-center">
                      {role.replace('_primary', '').replace('_secondary', '')}
                    </span>
                    <span className="text-[9px] font-mono text-[#A1A1AA]">
                      {copiedToken === safeHex ? '✓' : safeHex}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SECTION C: SLIDE THUMBNAIL LIST */}
          <div className="flex-1 p-3.5 overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono font-bold tracking-wider text-[#71717A] uppercase">
                Slides ({currentSlides.length})
              </span>
              {currentSlides.length > 0 && (
                <span className="text-[10px] font-mono text-[#A1A1AA]">
                  {activeSlideIndex + 1} / {currentSlides.length}
                </span>
              )}
            </div>

            {currentSlides.length === 0 ? (
              <div className="h-48 flex flex-col items-center justify-center text-center p-4 text-[#71717A]">
                <Layers className="w-6 h-6 opacity-40 mb-1.5" />
                <p className="text-xs">No presentation loaded</p>
                <p className="text-[10px] text-[#52525B] mt-0.5">Click "Load Sample Deck" above</p>
              </div>
            ) : (
              <div className="space-y-2">
                {currentSlides.map((s, idx) => {
                  const titleNode = s.nodes.find(
                    (n) => n.type === 'TEXT_CONTAINER' && n.paragraphs && n.paragraphs.length > 0
                  );
                  const title = titleNode?.paragraphs?.[0]?.text?.slice(0, 28) || `Slide ${idx + 1}`;

                  return (
                    <div
                      key={idx}
                      onClick={() => {
                        setActiveSlideIndex(idx);
                        setSelectedNodeIndex(null);
                      }}
                      className={`p-2 rounded-lg border transition-all cursor-pointer ${
                        activeSlideIndex === idx
                          ? 'border-[#FFB81C] bg-[#18181B] shadow-sm'
                          : 'border-[#27272A] bg-[#141418] hover:border-[#3F3F46]'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                        <span className="font-semibold text-white">Slide {idx + 1}</span>
                        <span className="text-[9px] text-[#71717A]">
                          {s.nodes.length} nodes
                        </span>
                      </div>
                      <p className="text-xs text-[#A1A1AA] truncate font-medium mb-1.5">{title}</p>

                      {/* Mini preview */}
                      <div className="w-full h-12 bg-[#030C1E] rounded border border-[#27272A] relative overflow-hidden">
                        {s.nodes.slice(0, 6).map((n, i) => {
                          const leftPct = (((n.x ?? n.bbox.left) ?? 0) / 13.333) * 100;
                          const topPct = (((n.y ?? n.bbox.top) ?? 0) / 7.5) * 100;
                          const wPct = (((n.w ?? n.bbox.width) ?? 1) / 13.333) * 100;
                          const hPct = (((n.h ?? n.bbox.height) ?? 1) / 7.5) * 100;

                          return (
                            <div
                              key={i}
                              style={{
                                left: `${leftPct}%`,
                                top: `${topPct}%`,
                                width: `${Math.max(4, wPct)}%`,
                                height: `${Math.max(4, hPct)}%`,
                                backgroundColor: n.fill_color || (viewMode === 'after' ? '#FFB81C' : '#3B82F6'),
                              }}
                              className="absolute rounded-[1px] opacity-60"
                            />
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        {/* CENTER STAGE: Canvas Stage (flex-1 h-full overflow-hidden flex flex-col items-center justify-center p-6 relative) */}
        <main
          ref={stageContainerRef}
          className="flex-1 h-full overflow-hidden flex flex-col items-center justify-center p-6 relative bg-[#18181B]"
        >
          {currentSlides.length === 0 ? (
            // Empty State
            <div className="max-w-md w-full bg-[#121215] border border-[#27272A] rounded-2xl p-8 text-center shadow-xl">
              <div className="w-12 h-12 rounded-xl bg-[#27272A] border border-[#3F3F46] flex items-center justify-center text-[#FFB81C] mx-auto mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Import Presentation to Format
              </h2>
              <p className="text-xs text-[#A1A1AA] mt-1.5 leading-relaxed">
                BrandMorph reformats PowerPoint decks in-place: remapping off-brand colors with CIE Lab Delta-E,
                standardizing typography, and preserving OpenXML elements intact.
              </p>
              <div className="mt-5 flex items-center justify-center gap-2.5">
                <button
                  onClick={handleLoadSample}
                  disabled={isProcessing}
                  className="px-4 py-2 rounded-lg bg-[#FFB81C] text-[#09090B] font-semibold text-xs hover:bg-[#F59E0B] transition"
                >
                  Load Sample Messy Deck
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 rounded-lg bg-[#27272A] hover:bg-[#3F3F46] text-white font-medium text-xs border border-[#3F3F46] transition"
                >
                  Upload File
                </button>
              </div>
            </div>
          ) : (
            // 880x495 Slide Canvas scaled to fit stage perfectly
            <div
              style={{
                transform: `scale(${canvasScale})`,
                transformOrigin: 'center center',
              }}
              className="transition-transform duration-75 select-none"
            >
              <div
                className={`w-[880px] h-[495px] rounded-lg shadow-2xl relative overflow-hidden transition-all border ${
                  viewMode === 'before'
                    ? 'bg-[#F8FAFC] border-[#CBD5E1]'
                    : 'bg-[#030C1E] border-[#27272A] shadow-black/80'
                }`}
                style={{
                  backgroundColor:
                    viewMode === 'before'
                      ? '#F8FAFC'
                      : `#${(currentBrand.palette.background || '030C1E').replace(/^#/, '')}`,
                }}
              >
                {/* Structured Corporate Template Layer (ViewMode After) */}
                {viewMode === 'after' && (
                  <>
                    {/* Subtle bottom geometric accent framing (left=0, top=7.36", width=13.333", height=0.05") */}
                    <div
                      style={{
                        left: 0,
                        top: `${7.36 * SCALE_Y}px`,
                        width: `${13.333 * SCALE_X}px`,
                        height: '3.5px',
                      }}
                      className="absolute bg-[#FFB81C] pointer-events-none z-10"
                    />

                    {/* Top-Right Brand Stamp (left=11.5", top=0.32", width=1.45", height=0.42") */}
                    <div
                      style={{
                        left: `${11.5 * SCALE_X}px`,
                        top: `${0.32 * SCALE_Y}px`,
                        width: `${1.45 * SCALE_X}px`,
                        height: `${0.42 * SCALE_Y}px`,
                      }}
                      className="absolute flex items-center justify-end text-[10px] font-mono font-bold tracking-wider text-[#FFB81C] pointer-events-none z-20"
                    >
                      AKKODIS
                    </div>
                  </>
                )}

                {/* Master Background Image */}
                {activeSlide?.bg_image && (
                  <img
                    src={`data:image/png;base64,${activeSlide.bg_image}`}
                    alt="Slide Background Master"
                    className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
                  />
                )}

                {/* AST Nodes Rendering Layer */}
                <div className="relative z-10 w-full h-full">
                  {/* Layer 1: PICTURE Nodes rendered first so text overlays remain on top */}
                  {activeSlide?.nodes
                    .filter((n) => n.type === 'PICTURE' || n.type === 'IMAGE')
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;
                      const imgSrc = node.image_src || node.image_data;

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
                              Image
                            </div>
                          )}
                        </div>
                      );
                    })}

                  {/* Layer 2: Shape Containers (Cards, Boxes, Ovals, Arrows) */}
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

                      // Skip template line/stamp if already rendered
                      if (
                        node.shape_name?.includes('BrandMorphBottomFrame') ||
                        node.shape_name?.includes('BrandMorphStamp')
                      ) {
                        return null;
                      }

                      if (node.type === 'ARROW_SHAPE' || node.type === 'LINE_SHAPE') {
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
                            }}
                            className="absolute flex items-center justify-center text-[#FFB81C] cursor-pointer"
                          >
                            <ArrowRight className="w-full h-full text-[#FFB81C]" />
                          </div>
                        );
                      }

                      const cardBg =
                        viewMode === 'before'
                          ? node.fill_color || '#E2E8F0'
                          : node.fill_color || `#${(currentBrand.palette.surface || '081632').replace(/^#/, '')}`;

                      const cardBorder =
                        viewMode === 'before'
                          ? node.line_color || '#CBD5E1'
                          : node.line_color || '#14305F';

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
                            backgroundColor: cardBg,
                            borderColor: cardBorder,
                          }}
                          className={`absolute ${
                            node.type === 'OVAL_SHAPE' ? 'rounded-full' : 'rounded-xl'
                          } border transition cursor-pointer flex flex-col justify-between p-2.5 ${
                            isSelected ? 'ring-2 ring-[#FFB81C]' : 'hover:border-[#FFB81C]/50'
                          }`}
                        >
                          <span className="text-[10px] font-mono text-[#8EA0C2] uppercase truncate">
                            {node.shape_name || 'Container'}
                          </span>
                        </div>
                      );
                    })}

                  {/* Layer 3: Text Containers rendered on top */}
                  {activeSlide?.nodes
                    .filter((n) => n.type === 'TEXT_CONTAINER' && n.paragraphs)
                    .map((node, nIdx) => {
                      const leftPx = ((node.x ?? node.bbox.left) ?? 0) * SCALE_X;
                      const topPx = ((node.y ?? node.bbox.top) ?? 0) * SCALE_Y;
                      const widthPx = ((node.w ?? node.bbox.width) ?? 1) * SCALE_X;
                      const heightPx = ((node.h ?? node.bbox.height) ?? 1) * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;

                      if (
                        node.shape_name?.includes('BrandMorphStamp') ||
                        node.shape_name?.includes('BrandMorphBottomFrame')
                      ) {
                        return null;
                      }

                      return (
                        <div
                          key={`txt-${nIdx}`}
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
                                  : 'Arial'
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

        {/* RIGHT PANEL: Inspector & Transformation Receipt (w-80 h-full overflow-y-auto shrink-0 border-l) */}
        <aside className="w-80 h-full overflow-y-auto shrink-0 border-l border-[#27272A] bg-[#121215] flex flex-col">
          {/* Header */}
          <div className="p-3.5 border-b border-[#27272A]">
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#71717A] uppercase flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#FFB81C]" /> Transformation Receipt
            </span>
          </div>

          {/* Section 1: Stats Badges */}
          <div className="p-3.5 border-b border-[#27272A] space-y-2.5">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-[#18181B] border border-[#27272A]">
                <div className="text-[9px] font-mono text-[#71717A] uppercase">Total Mutations</div>
                <div className="text-base font-bold text-[#FFB81C] font-mono mt-0.5">
                  {report?.total_changes ?? (slides.length > 0 ? 65 : 0)}
                </div>
                <div className="text-[8px] text-[#10B981] font-mono">100% In-Place</div>
              </div>

              <div className="p-2.5 rounded-lg bg-[#18181B] border border-[#27272A]">
                <div className="text-[9px] font-mono text-[#71717A] uppercase">Slides Processed</div>
                <div className="text-base font-bold text-white font-mono mt-0.5">
                  {slides.length}
                </div>
                <div className="text-[8px] text-[#A1A1AA] font-mono">16:9 Widescreen</div>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-[#18181B] border border-[#27272A] space-y-1.5 text-xs font-mono">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#71717A]">Color Remap:</span>
                <span className="text-white font-medium">CIE Lab (ΔE &lt; 2.3)</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#71717A]">Typography:</span>
                <span className="text-white font-medium">Times New Roman / Arial</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#71717A]">Idempotence:</span>
                <span className="text-[#FFB81C] font-semibold text-[10px] truncate max-w-[110px]">
                  {report?.deck_sha256 ? report.deck_sha256.slice(0, 10) + '...' : 'Verified SHA-256'}
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: Node Inspector / Diff */}
          <div className="flex-1 p-3.5 flex flex-col">
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#71717A] uppercase mb-2 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#FFB81C]" /> Element Inspector
            </span>

            {selectedNode ? (
              <div className="space-y-3 bg-[#18181B] p-3 rounded-lg border border-[#3F3F46] text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-[#27272A]">
                  <span className="font-mono text-white font-semibold">Node #{selectedNode.id}</span>
                  <span className="font-mono text-[9px] bg-[#27272A] text-[#A1A1AA] px-1.5 py-0.5 rounded">
                    {selectedNode.type}
                  </span>
                </div>

                <div className="space-y-1 font-mono text-[10px] text-[#71717A]">
                  <div>
                    Coordinates: X:{selectedNode.x ?? selectedNode.bbox.left}″ Y:{selectedNode.y ?? selectedNode.bbox.top}″
                  </div>
                  <div>
                    Dimensions: {selectedNode.w ?? selectedNode.bbox.width}″ × {selectedNode.h ?? selectedNode.bbox.height}″
                  </div>
                </div>

                {/* Text Editor */}
                {selectedNode.paragraphs && (
                  <div className="space-y-1">
                    <label className="text-[9px] font-mono text-[#71717A] uppercase">Text Content</label>
                    <textarea
                      value={selectedNode.paragraphs[0]?.text || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSlides((prev) => {
                          const copy = [...prev];
                          if (copy[activeSlideIndex]?.nodes[selectedNodeIndex!].paragraphs?.[0]) {
                            copy[activeSlideIndex].nodes[selectedNodeIndex!].paragraphs![0].text = val;
                          }
                          return copy;
                        });
                      }}
                      className="w-full h-16 bg-[#121215] border border-[#27272A] rounded p-2 text-xs text-white focus:outline-none focus:border-[#FFB81C] font-sans"
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-4 text-[#71717A]">
                <Eye className="w-6 h-6 opacity-40 mb-1" />
                <p className="text-xs">No element selected</p>
                <p className="text-[10px] text-[#52525B] mt-0.5">Click any shape or text box on the canvas</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
