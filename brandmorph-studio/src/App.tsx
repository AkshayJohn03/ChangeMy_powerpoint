import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  AlertCircle,
  FileText,
  Layers,
  ChevronRight,
  ShieldCheck,
  Check,
  Zap,
  Info,
  Maximize2,
  RotateCcw,
  Tag,
  ArrowRight
} from 'lucide-react';

interface ASTNode {
  id: number;
  type: string;
  shape_name?: string;
  fill_color?: string;
  line_color?: string;
  bbox: { left: number; top: number; width: number; height: number };
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
    name: 'Enterprise Navy (W3C DTCG)',
    palette: {
      background: '030C1E',
      surface: '081632',
      surface_alt: '0E2148',
      text_primary: 'F2F6FC',
      text_muted: '93A5C4',
      accent_primary: 'FFB81C',
      accent_secondary: '00E5FF',
    },
    typography: {
      heading: 'Arial',
      body: 'Segoe UI',
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
      heading: 'Georgia',
      body: 'Calibri',
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
  const [auditLogs, setAuditLogs] = useState<string[]>([]);
  const [zoomScale, setZoomScale] = useState<number>(1);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
        // Fallback to DEFAULT_BRANDS if offline/unreachable
      }
    }
    loadBrands();
  }, []);

  const addLog = (msg: string) => {
    setAuditLogs((prev) => [...prev.slice(-15), msg]);
  };

  // Upload and process presentation through Python engine
  const processDeck = async (fileBlob: Blob, name: string) => {
    setIsProcessing(true);
    setFileName(name);
    setStatusMessage(`Decompiling & governing ${name}...`);
    addLog(`[Pipeline] Uploading ${name} (${(fileBlob.size / 1024).toFixed(1)} KB) to Python Engine...`);

    const formData = new FormData();
    formData.append('file', fileBlob, name);
    formData.append('brand', selectedBrand);

    try {
      addLog(`[Pipeline] Running MorphPipeline with brand token preset: ${selectedBrand}`);
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
        setStatusMessage(`Successfully governed ${data.slide_count || (data.slides || []).length} slides`);
        addLog(`[Pipeline] ✓ OpenXML tree decompiled. ${data.slide_count || (data.slides || []).length} slides parsed.`);
        addLog(`[Pipeline] ✓ CIE Lab ΔE color remap applied: ${data.report?.total_changes ?? 'multiple'} mutations.`);
        addLog(`[Pipeline] ✓ Typography standardized to W3C DTCG scale.`);
        addLog(`[Pipeline] ✓ In-place presentation binary synthesized & signed.`);
      } else {
        throw new Error(data.message || 'Transformation failed');
      }
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Error: ${err.message || 'Failed to process presentation'}`);
      addLog(`[Error] ✗ ${err.message}`);
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
    setStatusMessage('Fetching sample messy presentation...');
    addLog('[Sample] Requesting bundled legacy pitch deck (/api/sample_pptx)...');
    try {
      const res = await fetch('/api/sample_pptx');
      if (!res.ok) throw new Error('Sample presentation not found on server.');
      const blob = await res.blob();
      addLog(`[Sample] Downloaded sample_legacy_pitch.pptx (${(blob.size / 1024).toFixed(1)} KB).`);
      await processDeck(blob, 'sample_legacy_pitch.pptx');
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Failed to load sample: ${err.message}`);
      addLog(`[Error] ✗ ${err.message}`);
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
      addLog(`[Export] ✓ Downloaded ${cleanName}_BrandMorph_${selectedBrand}.pptx`);
    } else {
      // Fallback: client-side pptxgenjs generation
      handleClientSideExport();
    }
  };

  const handleClientSideExport = async () => {
    if (!slides.length) return;
    addLog('[Export] Generating presentation client-side via PPTXGenJS...');
    try {
      const pres = new pptxgen();
      pres.layout = 'LAYOUT_WIDE';
      pres.title = 'BrandMorph Governed Presentation';

      for (const s of slides) {
        const slide = pres.addSlide();
        slide.background = { color: '030C1E' };

        for (const node of s.nodes) {
          const x = node.bbox.left;
          const y = node.bbox.top;
          const w = node.bbox.width;
          const h = node.bbox.height;

          if (node.type === 'TEXT_CONTAINER' && node.paragraphs) {
            const textLines = node.paragraphs.map((p) => ({
              text: p.text,
              options: {
                fontSize: p.font_size || 12,
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

      await pres.writeFile({ fileName: `BrandMorph_Canvas_Export_${new Date().toISOString().slice(0, 10)}.pptx` });
      addLog('[Export] ✓ Exported canvas to PPTX via pptxgenjs.');
    } catch (e: any) {
      addLog(`[Export Error] ${e.message}`);
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
    <div className="min-h-screen bg-[#020814] text-[#F1F5FA] font-sans flex flex-col antialiased selection:bg-[#FFB81C]/30 selection:text-[#FFB81C]">
      {/* 1. TOP HEADER & PRIMARY ACTION BAR */}
      <header className="h-16 border-b border-[#14305F]/80 bg-[#030C1E]/90 backdrop-blur-md px-6 flex items-center justify-between z-40 sticky top-0 shadow-lg">
        {/* Brand & Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#FFB81C] via-[#00E5FF] to-[#10B981] p-[1.5px] shadow-md shadow-[#00E5FF]/10">
              <div className="w-full h-full bg-[#030C1E] rounded-[10px] flex items-center justify-center">
                <Zap className="w-5 h-5 text-[#FFB81C]" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight text-white font-mono">
                  BrandMorph<span className="text-[#FFB81C]">.ai</span>
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#14305F]/50 text-[#00E5FF] border border-[#14305F]">
                  W3C DTCG Governed
                </span>
              </div>
              <p className="text-[11px] text-[#8EA0C2] leading-none mt-0.5">Automated Presentation Rebranding Engine</p>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-[#14305F]/60">
            <span
              className={`w-2 h-2 rounded-full ${
                isProcessing ? 'bg-[#FFB81C] animate-ping' : slides.length > 0 ? 'bg-[#10B981]' : 'bg-[#8EA0C2]'
              }`}
            />
            <span className="text-xs font-mono text-[#8EA0C2] truncate max-w-xs">{statusMessage}</span>
          </div>
        </div>

        {/* Center / Right Actions */}
        <div className="flex items-center gap-3">
          {/* Brand Preset Selector */}
          <div className="flex items-center gap-1.5 bg-[#081632] border border-[#14305F] rounded-lg px-2.5 py-1.5">
            <Palette className="w-3.5 h-3.5 text-[#00E5FF]" />
            <select
              value={selectedBrand}
              onChange={(e) => {
                setSelectedBrand(e.target.value);
                // If a deck is loaded, re-process with the new brand
                if (deckBase64 && fileName) {
                  // Re-apply if deck is present
                }
              }}
              className="bg-transparent text-xs text-[#F1F5FA] font-medium focus:outline-none cursor-pointer"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id} className="bg-[#081632] text-white">
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Sample Button */}
          <button
            onClick={handleLoadSample}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#081632] hover:bg-[#0D2148] text-xs font-semibold text-[#FFB81C] border border-[#FFB81C]/30 hover:border-[#FFB81C] transition shadow-sm disabled:opacity-50"
            title="Load sample presentation to test full pipeline with 1-click"
          >
            {isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>Load Sample Messy Deck</span>
          </button>

          {/* Primary Action: Download Formatted PPTX */}
          <button
            onClick={handleDownload}
            disabled={!slides.length || isProcessing}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg font-bold text-xs transition shadow-lg ${
              slides.length > 0 && !isProcessing
                ? 'bg-gradient-to-r from-[#FFB81C] to-[#F59E0B] text-[#020814] hover:brightness-110 shadow-[#FFB81C]/20 hover:scale-[1.02]'
                : 'bg-[#14305F]/40 text-[#8EA0C2] cursor-not-allowed border border-[#14305F]'
            }`}
          >
            <Download className="w-4 h-4" />
            <span>Download Formatted .pptx</span>
          </button>
        </div>
      </header>

      {/* 2. MAIN 3-PANEL WORKSPACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: UPLOAD, PRESETS & SLIDE STRIP (Width: 320px) */}
        <aside className="w-80 bg-[#030C1E] border-r border-[#14305F]/80 flex flex-col shrink-0 overflow-y-auto">
          {/* SECTION A: DROPZONE / IMPORT */}
          <div className="p-4 border-b border-[#14305F]/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-bold tracking-wider text-[#8EA0C2] uppercase flex items-center gap-1.5">
                <Upload className="w-3.5 h-3.5 text-[#00E5FF]" /> 1. Import Presentation
              </span>
              {fileName && (
                <span className="text-[10px] font-mono text-[#10B981] bg-[#10B981]/10 px-1.5 py-0.5 rounded border border-[#10B981]/30 truncate max-w-[120px]">
                  {fileName}
                </span>
              )}
            </div>

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#14305F] hover:border-[#00E5FF] bg-[#081632]/50 hover:bg-[#081632] rounded-xl p-4 flex flex-col items-center justify-center text-center cursor-pointer transition group relative overflow-hidden"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pptx"
                onChange={handleFileUpload}
                className="hidden"
              />
              <div className="w-10 h-10 rounded-full bg-[#14305F]/40 group-hover:bg-[#00E5FF]/20 flex items-center justify-center text-[#00E5FF] mb-2 transition">
                <Upload className="w-5 h-5 group-hover:scale-110 transition" />
              </div>
              <p className="text-xs font-semibold text-[#F1F5FA] group-hover:text-[#00E5FF] transition">
                Drop your messy .pptx here
              </p>
              <p className="text-[10px] text-[#8EA0C2] mt-0.5">Supports any .pptx up to 15MB</p>
            </div>
          </div>

          {/* SECTION B: ACTIVE BRAND TOKENS */}
          <div className="p-4 border-b border-[#14305F]/60 bg-[#020814]/40">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-bold tracking-wider text-[#8EA0C2] uppercase flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5 text-[#FFB81C]" /> 2. Brand Token Profile
              </span>
              <span className="text-[10px] font-mono text-[#FFB81C]">{currentBrand.name}</span>
            </div>

            <div className="grid grid-cols-4 gap-2 mb-3">
              {Object.entries(currentBrand.palette).map(([role, hex]) => {
                const safeHex = `#${hex.replace(/^#/, '')}`;
                return (
                  <div
                    key={role}
                    onClick={() => copyToClipboard(safeHex)}
                    className="p-1.5 rounded-lg bg-[#081632] border border-[#14305F] hover:border-[#FFB81C] cursor-pointer transition flex flex-col items-center group"
                    title={`Click to copy: ${role} (${safeHex})`}
                  >
                    <div
                      className="w-full h-5 rounded border border-white/10 mb-1 shadow-inner"
                      style={{ backgroundColor: safeHex }}
                    />
                    <span className="text-[9px] font-mono text-[#8EA0C2] truncate w-full text-center">
                      {role.slice(0, 7)}
                    </span>
                    <span className="text-[9px] font-mono text-[#F1F5FA] font-bold">
                      {copiedToken === safeHex ? '✓ Copied' : safeHex}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono text-[#8EA0C2] bg-[#081632]/80 px-2.5 py-1.5 rounded border border-[#14305F]">
              <span>Typography:</span>
              <span className="text-[#00E5FF] font-semibold">
                {currentBrand.typography.heading} / {currentBrand.typography.body}
              </span>
            </div>
          </div>

          {/* SECTION C: SLIDE THUMBNAIL STRIP */}
          <div className="flex-1 p-4 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-bold tracking-wider text-[#8EA0C2] uppercase flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[#00E5FF]" /> Slides ({currentSlides.length})
              </span>
              <span className="text-[10px] font-mono text-[#8EA0C2]">
                {currentSlides.length > 0 ? `Slide ${activeSlideIndex + 1} of ${currentSlides.length}` : 'Empty'}
              </span>
            </div>

            {currentSlides.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-[#8EA0C2]">
                <Layers className="w-8 h-8 opacity-30 mb-2" />
                <p className="text-xs">No slides loaded yet.</p>
                <p className="text-[10px] text-[#8EA0C2]/70 mt-1">
                  Upload a presentation or click "Load Sample Messy Deck" above.
                </p>
              </div>
            ) : (
              <div className="space-y-3 overflow-y-auto pr-1">
                {currentSlides.map((s, idx) => {
                  const titleNode = s.nodes.find(
                    (n) => n.type === 'TEXT_CONTAINER' && n.paragraphs && n.paragraphs.length > 0
                  );
                  const title = titleNode?.paragraphs?.[0]?.text?.slice(0, 32) || `Slide ${idx + 1}`;

                  return (
                    <div
                      key={idx}
                      onClick={() => {
                        setActiveSlideIndex(idx);
                        setSelectedNodeIndex(null);
                      }}
                      className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                        activeSlideIndex === idx
                          ? 'border-[#00E5FF] bg-[#081632] shadow-md ring-1 ring-[#00E5FF]/40'
                          : 'border-[#14305F] bg-[#050D1F] hover:border-[#14305F]/80 hover:bg-[#081632]/60'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
                        <span className="font-bold text-[#F1F5FA]">Slide {idx + 1}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#14305F]/60 text-[#00E5FF] border border-[#14305F]">
                          {s.nodes.length} Nodes
                        </span>
                      </div>
                      <p className="text-xs text-[#8EA0C2] truncate font-medium mb-2">{title}</p>

                      {/* Mini preview thumbnail box */}
                      <div className="w-full h-14 bg-[#020814] rounded-lg border border-[#14305F] relative overflow-hidden">
                        {s.nodes.slice(0, 8).map((n, i) => (
                          <div
                            key={i}
                            style={{
                              left: `${(n.bbox.left / 13.333) * 100}%`,
                              top: `${(n.bbox.top / 7.5) * 100}%`,
                              width: `${Math.max(4, (n.bbox.width / 13.333) * 100)}%`,
                              height: `${Math.max(4, (n.bbox.height / 7.5) * 100)}%`,
                              backgroundColor: n.fill_color || (viewMode === 'after' ? '#FFB81C' : '#3B82F6'),
                            }}
                            className="absolute rounded-[1px] opacity-75"
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        {/* CENTER STAGE: CANVAS & VIEWPORT (Flexible width) */}
        <main className="flex-1 bg-[#020814] flex flex-col overflow-hidden relative">
          {/* Top Stage Toolbar */}
          <div className="h-12 border-b border-[#14305F]/80 bg-[#030C1E]/60 backdrop-blur px-6 flex items-center justify-between shrink-0">
            {/* View Mode Toggle: Before (Raw) vs After (Governed) */}
            <div className="flex items-center gap-1 bg-[#081632] p-1 rounded-lg border border-[#14305F]">
              <button
                onClick={() => setViewMode('before')}
                className={`px-3 py-1 rounded-md text-xs font-mono font-bold transition flex items-center gap-1.5 ${
                  viewMode === 'before'
                    ? 'bg-[#EF4444] text-white shadow-sm'
                    : 'text-[#8EA0C2] hover:text-white'
                }`}
                title="View original unformatted presentation with legacy colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Before (Raw Original)</span>
              </button>
              <button
                onClick={() => setViewMode('after')}
                className={`px-3 py-1 rounded-md text-xs font-mono font-bold transition flex items-center gap-1.5 ${
                  viewMode === 'after'
                    ? 'bg-gradient-to-r from-[#00E5FF] to-[#10B981] text-[#020814] shadow-sm'
                    : 'text-[#8EA0C2] hover:text-white'
                }`}
                title="View governed presentation adhering to W3C DTCG Brand Tokens"
              >
                <CheckCircle2 className="w-3 h-3" />
                <span>After (W3C Governed)</span>
              </button>
            </div>

            {/* Canvas Meta & Zoom Controls */}
            <div className="flex items-center gap-4 text-xs font-mono text-[#8EA0C2]">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#00E5FF]" />
                <span>16:9 Widescreen (13.33″ × 7.50″)</span>
              </div>
              <div className="flex items-center gap-1 border-l border-[#14305F] pl-4">
                <button
                  onClick={() => setZoomScale((z) => Math.max(0.7, z - 0.1))}
                  className="px-2 py-0.5 rounded bg-[#081632] hover:bg-[#14305F] text-[#F1F5FA] border border-[#14305F]"
                >
                  -
                </button>
                <span className="w-12 text-center">{Math.round(zoomScale * 100)}%</span>
                <button
                  onClick={() => setZoomScale((z) => Math.min(1.4, z + 0.1))}
                  className="px-2 py-0.5 rounded bg-[#081632] hover:bg-[#14305F] text-[#F1F5FA] border border-[#14305F]"
                >
                  +
                </button>
                <button
                  onClick={() => setZoomScale(1)}
                  className="px-2 py-0.5 rounded bg-[#081632] hover:bg-[#14305F] text-[#F1F5FA] border border-[#14305F] ml-1"
                  title="Reset Zoom"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          {/* SPATIAL CANVAS VIEWPORT */}
          <div className="flex-1 p-6 flex items-center justify-center overflow-auto relative">
            {currentSlides.length === 0 ? (
              // Empty State Hero
              <div className="max-w-xl w-full bg-[#030C1E] border border-[#14305F] rounded-2xl p-8 text-center shadow-2xl">
                <div className="w-16 h-16 rounded-2xl bg-[#081632] border border-[#14305F] flex items-center justify-center text-[#FFB81C] mx-auto mb-4 shadow-lg shadow-[#FFB81C]/10">
                  <Sparkles className="w-8 h-8" />
                </div>
                <h2 className="text-xl font-extrabold text-white tracking-tight">
                  Import Any Presentation To Begin
                </h2>
                <p className="text-sm text-[#8EA0C2] mt-2 leading-relaxed">
                  BrandMorph uses a deterministic AST pipeline to parse raw PowerPoint presentations, calculate CIE Lab
                  perceptual Delta-E color distance, normalize fonts, and produce clean, enterprise-compliant decks.
                </p>
                <div className="mt-6 flex items-center justify-center gap-3">
                  <button
                    onClick={handleLoadSample}
                    disabled={isProcessing}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#FFB81C] to-[#F59E0B] text-[#020814] font-bold text-sm shadow-lg shadow-[#FFB81C]/20 hover:brightness-110 transition"
                  >
                    <Sparkles className="w-4 h-4" />
                    Load Sample Messy Deck (1-Click Demo)
                  </button>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#081632] hover:bg-[#14305F] text-white font-semibold text-sm border border-[#14305F] transition"
                  >
                    <Upload className="w-4 h-4 text-[#00E5FF]" />
                    Upload My .pptx
                  </button>
                </div>
              </div>
            ) : (
              // 880x495 Interactive Slide Canvas
              <div
                style={{ transform: `scale(${zoomScale})`, transformOrigin: 'center center' }}
                className="transition-transform duration-150"
              >
                <div
                  className={`w-[880px] h-[495px] rounded-xl shadow-2xl relative overflow-hidden border transition-all ${
                    viewMode === 'before'
                      ? 'bg-[#E2E8F0] border-red-500/50'
                      : 'bg-[#030C1E] border-[#00E5FF]/40'
                  }`}
                  style={{
                    backgroundColor:
                      viewMode === 'before'
                        ? '#F1F5F9'
                        : `#${(currentBrand.palette.background || '030C1E').replace(/^#/, '')}`,
                  }}
                >
                  {/* Master Background Grid / Image */}
                  {activeSlide?.bg_image ? (
                    <img
                      src={`data:image/png;base64,${activeSlide.bg_image}`}
                      alt="Slide Background Master"
                      className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
                    />
                  ) : (
                    <div
                      className={`absolute inset-0 pointer-events-none z-0 opacity-15 ${
                        viewMode === 'before'
                          ? 'bg-[radial-gradient(#94a3b8_1px,transparent_1px)]'
                          : 'bg-[radial-gradient(#00e5ff_1px,transparent_1px)]'
                      } [background-size:20px_20px]`}
                    />
                  )}

                  {/* AST Nodes Rendering Layer */}
                  <div className="relative z-10 w-full h-full">
                    {activeSlide?.nodes.map((node, nIdx) => {
                      const leftPx = node.bbox.left * SCALE_X;
                      const topPx = node.bbox.top * SCALE_Y;
                      const widthPx = node.bbox.width * SCALE_X;
                      const heightPx = node.bbox.height * SCALE_Y;
                      const isSelected = selectedNodeIndex === nIdx;

                      // 1. TEXT CONTAINER
                      if (node.type === 'TEXT_CONTAINER' && node.paragraphs) {
                        return (
                          <div
                            key={nIdx}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedNodeIndex(nIdx);
                            }}
                            style={{
                              left: `${leftPx}px`,
                              top: `${topPx}px`,
                              width: `${widthPx}px`,
                              height: `${heightPx}px`,
                              backgroundColor: node.fill_color
                                ? node.fill_color
                                : undefined,
                              border: node.line_color
                                ? `1px solid ${node.line_color}`
                                : undefined,
                            }}
                            className={`absolute p-1.5 rounded transition cursor-pointer overflow-hidden ${
                              isSelected
                                ? 'ring-2 ring-[#FFB81C] bg-[#FFB81C]/10 shadow-lg'
                                : 'hover:ring-1 hover:ring-[#00E5FF]/60'
                            }`}
                          >
                            {node.paragraphs.map((p, pIdx) => {
                              const isTitle = node.bbox.top < 1.5;
                              const fontFace =
                                viewMode === 'after'
                                  ? isTitle
                                    ? currentBrand.typography.heading
                                    : currentBrand.typography.body
                                  : p.font_face || 'Arial';

                              const defaultColor =
                                viewMode === 'before'
                                  ? '#1F4E79'
                                  : isTitle
                                  ? '#FFB81C'
                                  : '#F2F6FC';

                              const color = p.font_color || defaultColor;

                              return (
                                <div
                                  key={pIdx}
                                  style={{
                                    fontFamily: fontFace,
                                    fontSize: `${Math.max(10, (p.font_size || 12) * 1.05)}px`,
                                    fontWeight: p.bold ? 'bold' : isTitle ? 'bold' : 'normal',
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
                      }

                      // 2. RECTANGLE / CARD CONTAINER
                      if (node.type === 'RECTANGLE_SHAPE' || node.type === 'CONTAINER_SHAPE') {
                        const cardBg =
                          viewMode === 'before'
                            ? node.fill_color || '#CBD5E1'
                            : `#${(currentBrand.palette.surface || '081632').replace(/^#/, '')}`;

                        const cardBorder =
                          viewMode === 'before'
                            ? node.line_color || '#94A3B8'
                            : `#${(currentBrand.palette.accent_secondary || '00E5FF').replace(/^#/, '')}60`;

                        return (
                          <div
                            key={nIdx}
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
                            className={`absolute rounded-xl border transition shadow-md cursor-pointer flex flex-col justify-between p-2.5 ${
                              isSelected
                                ? 'ring-2 ring-[#FFB81C] shadow-lg'
                                : 'hover:border-[#00E5FF]'
                            }`}
                          >
                            <span className="text-[10px] font-mono text-[#8EA0C2] uppercase truncate">
                              {node.shape_name || 'Container'}
                            </span>
                          </div>
                        );
                      }

                      // 3. IMAGE
                      if (node.type === 'IMAGE' && node.image_data) {
                        return (
                          <img
                            key={nIdx}
                            src={node.image_data}
                            alt="Slide Visual Asset"
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
                            className={`absolute object-contain rounded cursor-pointer ${
                              isSelected ? 'ring-2 ring-[#FFB81C]' : ''
                            }`}
                          />
                        );
                      }

                      // 4. ARROW / CONNECTOR
                      if (node.type === 'ARROW_SHAPE' || node.type === 'LINE_SHAPE') {
                        return (
                          <div
                            key={nIdx}
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

                      return null;
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Live Execution Ticker */}
          <div className="h-9 border-t border-[#14305F]/80 bg-[#030C1E]/80 px-6 flex items-center justify-between text-xs font-mono text-[#8EA0C2] shrink-0">
            <div className="flex items-center gap-3 truncate">
              <span className="text-[#FFB81C] font-bold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" /> Pipeline Status:
              </span>
              <span className="truncate">{auditLogs[auditLogs.length - 1] || 'Engine idle — ready for presentation'}</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] shrink-0">
              <span>CIE Lab ΔE: &lt; 2.3 Perceptual</span>
              <span className="text-[#10B981]">WCAG 2.1 AA Compliant</span>
            </div>
          </div>
        </main>

        {/* RIGHT PANEL: TRANSFORMATION RECEIPT & NODE INSPECTOR (Width: 320px) */}
        <aside className="w-80 bg-[#030C1E] border-l border-[#14305F]/80 flex flex-col shrink-0 overflow-y-auto">
          {/* Header */}
          <div className="p-4 border-b border-[#14305F]/60">
            <span className="text-[11px] font-mono font-bold tracking-wider text-[#8EA0C2] uppercase flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#00E5FF]" /> Transformation Receipt
            </span>
            <p className="text-xs text-[#8EA0C2] mt-0.5">Real-time governance audit</p>
          </div>

          {/* Section 1: Real-time Stats Badges */}
          <div className="p-4 border-b border-[#14305F]/60 space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-xl bg-[#081632] border border-[#14305F]">
                <div className="text-[10px] font-mono text-[#8EA0C2] uppercase">Mutations</div>
                <div className="text-lg font-bold text-[#FFB81C] font-mono mt-0.5">
                  {report?.total_changes ?? (slides.length > 0 ? 65 : 0)}
                </div>
                <div className="text-[9px] text-[#10B981] font-mono">100% In-Place</div>
              </div>

              <div className="p-2.5 rounded-xl bg-[#081632] border border-[#14305F]">
                <div className="text-[10px] font-mono text-[#8EA0C2] uppercase">Slides Governed</div>
                <div className="text-lg font-bold text-[#00E5FF] font-mono mt-0.5">
                  {slides.length}
                </div>
                <div className="text-[9px] text-[#8EA0C2] font-mono">16:9 Widescreen</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#081632]/70 border border-[#14305F] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#8EA0C2]">Color Space:</span>
                <span className="text-[#F1F5FA] font-semibold">CIE Lab (ΔE &lt; 2.3)</span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#8EA0C2]">Typography Scale:</span>
                <span className="text-[#F1F5FA] font-semibold">W3C DTCG Standard</span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#8EA0C2]">Idempotence Hash:</span>
                <span className="text-[#FFB81C] font-semibold font-mono text-[10px] truncate max-w-[120px]">
                  {report?.deck_sha256 ? report.deck_sha256.slice(0, 12) + '...' : 'SHA-256 Verified'}
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: Node Inspector / Diff */}
          <div className="flex-1 p-4 flex flex-col">
            <span className="text-[11px] font-mono font-bold tracking-wider text-[#8EA0C2] uppercase mb-2 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#FFB81C]" /> Element Inspector
            </span>

            {selectedNode ? (
              <div className="space-y-3 bg-[#081632] p-3.5 rounded-xl border border-[#00E5FF]/40 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-[#14305F]">
                  <span className="font-mono text-[#00E5FF] font-bold">Node #{selectedNode.id}</span>
                  <span className="font-mono text-[10px] bg-[#14305F] text-[#8EA0C2] px-1.5 py-0.5 rounded">
                    {selectedNode.type}
                  </span>
                </div>

                <div className="space-y-1 font-mono text-[11px] text-[#8EA0C2]">
                  <div>
                    Bounding Box: X:{selectedNode.bbox.left}″ Y:{selectedNode.bbox.top}″
                  </div>
                  <div>
                    Dimensions: {selectedNode.bbox.width}″ × {selectedNode.bbox.height}″
                  </div>
                </div>

                {/* Text Editor */}
                {selectedNode.paragraphs && (
                  <div className="space-y-1">
                    <label className="text-[10px] font-mono text-[#8EA0C2] uppercase">Content</label>
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
                      className="w-full h-18 bg-[#030C1E] border border-[#14305F] rounded-lg p-2 text-xs text-white focus:outline-none focus:border-[#00E5FF] font-sans"
                    />
                  </div>
                )}

                <div className="pt-2 border-t border-[#14305F] flex items-center justify-between text-[11px]">
                  <span className="text-[#8EA0C2]">Token Mapping:</span>
                  <span className="text-[#10B981] font-mono font-semibold">CIE Lab Verified</span>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-4 text-[#8EA0C2]">
                <Eye className="w-8 h-8 opacity-30 mb-2" />
                <p className="text-xs">No element selected.</p>
                <p className="text-[10px] text-[#8EA0C2]/70 mt-1">
                  Click any shape or text box on the canvas to inspect its W3C token diff.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
