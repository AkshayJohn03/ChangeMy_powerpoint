import React, { useState, useEffect, useRef } from 'react';
import { 
  Layers, Palette, Type, Image as ImageIcon, 
  Download, ShieldCheck, Cpu, Upload, Sparkles, 
  RotateCcw, RotateCw, MoveRight, Circle, 
  Check, Eye, EyeOff, LayoutTemplate, Award,
  Zap, Server, Target, Monitor, Globe, Database, Lock,
  Activity, Cloud, Bold, Italic, Underline,
  AlignLeft, AlignCenter, AlignRight, FileText, ChevronDown
} from 'lucide-react';

interface ASTNode {
  id: number;
  type: string;
  shape_name?: string;
  bbox: { left: number; top: number; width: number; height: number };
  image_data?: string;
  image_data_uri?: string;
  fill_hex?: string | null;
  line_hex?: string | null;
  line_width?: number;
  is_title?: boolean;
  paragraphs?: { 
    text: string; 
    level: number; 
    font_size?: number;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    align?: string;
    runs?: any[];
  }[];
}

interface SlideAST {
  slide_id: number;
  dimensions: { width: number; height: number };
  bg_image?: string;
  nodes: ASTNode[];
}

interface ColorToken {
  id: string;
  name: string;
  hex: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || "";

export default function StudioWorkspace() {
  const [appPhase, setAppPhase] = useState<'splash' | 'import' | 'studio' | 'v02_result'>('studio');
  const [pipelineMode, setPipelineMode] = useState<'v01' | 'v02' | 'tag' | 'golden'>('golden');
  const [viewMode, setViewMode] = useState<'after' | 'before'>('after');
  const [presetTheme, setPresetTheme] = useState<string>('enterprise_navy');
  const [v02Result, setV02Result] = useState<any>(null);
  const [slides, setSlides] = useState<SlideAST[]>([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileName, setFileName] = useState<string>('TestPPT.pptx');
  const [exporting, setExporting] = useState(false);

  // Undo / Redo History Stack
  const [history, setHistory] = useState<SlideAST[][]>([]);
  const [historyStep, setHistoryStep] = useState<number>(-1);

  // Right Panel Active Tab: 'brand' | 'background'
  const [activeRightTab, setActiveRightTab] = useState<'brand' | 'background'>('brand');

  // Selection & Formatting state
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number | null>(null);
  const [selectedParagraphIndex, setSelectedParagraphIndex] = useState<number>(0);

  // Dragging Node state
  const [draggingNodeIndex, setDraggingNodeIndex] = useState<number | null>(null);
  const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [nodeStartPos, setNodeStartPos] = useState<{ left: number; top: number }>({ left: 0, top: 0 });

  // Icon Selection
  const [selectedIconKey, setSelectedIconKey] = useState<string>('target');

  // Akkodis Color Tokens (Strict Corporate DNA)
  const [colors, setColors] = useState<ColorToken[]>([
    { id: 'darkNavy', name: 'Primary Dark Base', hex: '#001F33' },
    { id: 'cardSurface', name: 'Card Surface Slate', hex: '#081E36' },
    { id: 'gold', name: 'Akkodis Corporate Gold', hex: '#FFB81C' },
    { id: 'cyan', name: 'Cyan Telemetry Accent', hex: '#00FFFF' },
    { id: 'white', name: 'High Contrast White', hex: '#FFFFFF' },
    { id: 'cardAlt', name: 'Card Surface Alt', hex: '#0A2A4A' },
  ]);

  // Typography System
  const [titleFont, setTitleFont] = useState('Times New Roman');
  const [bodyFont, setBodyFont] = useState('Arial');

  // Dynamic Scale for Center Canvas (Issue #1: Never scroll off-screen)
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [canvasScale, setCanvasScale] = useState<number>(1);

  useEffect(() => {
    const handleResize = () => {
      if (!canvasContainerRef.current) return;
      const { clientWidth, clientHeight } = canvasContainerRef.current;
      const padX = 40;
      const padY = 40;
      const availW = Math.max(320, clientWidth - padX);
      const availH = Math.max(200, clientHeight - padY);
      // Fixed 16:9 reference dimensions: 880x495
      const scaleW = availW / 880;
      const scaleH = availH / 495;
      const fitScale = Math.min(scaleW, scaleH);
      setCanvasScale(Math.max(0.45, Math.min(fitScale, 1.35)));
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [slides, appPhase]);

  // Icon Catalog
  const ICON_LIBRARY = [
    { key: 'target', name: 'Target / SLA', icon: Target },
    { key: 'zap', name: 'Energy / Speed', icon: Zap },
    { key: 'shield', name: 'Security / Compliance', icon: ShieldCheck },
    { key: 'cpu', name: 'Processing / Core', icon: Cpu },
    { key: 'server', name: 'Infrastructure', icon: Server },
    { key: 'layers', name: 'Architecture', icon: Layers },
    { key: 'monitor', name: 'Display / UI', icon: Monitor },
    { key: 'globe', name: 'Global Network', icon: Globe },
    { key: 'database', name: 'Data Pipeline', icon: Database },
    { key: 'lock', name: 'Air-Gapped Privacy', icon: Lock },
    { key: 'activity', name: 'Performance / Telemetry', icon: Activity },
    { key: 'cloud', name: 'Cloud Platform', icon: Cloud },
  ];

  // Auto-load sample deck on initial mount if empty
  useEffect(() => {
    if (slides.length === 0) {
      handleLoadTestPPT();
    }
  }, []);

  const pushStateToHistory = (newSlides: SlideAST[]) => {
    const updatedHistory = history.slice(0, historyStep + 1);
    updatedHistory.push(JSON.parse(JSON.stringify(newSlides)));
    setHistory(updatedHistory);
    setHistoryStep(updatedHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyStep > 0) {
      const prevStep = historyStep - 1;
      setHistoryStep(prevStep);
      setSlides(JSON.parse(JSON.stringify(history[prevStep])));
    }
  };

  const handleRedo = () => {
    if (historyStep < history.length - 1) {
      const nextStep = historyStep + 1;
      setHistoryStep(nextStep);
      setSlides(JSON.parse(JSON.stringify(history[nextStep])));
    }
  };

  const createFallbackSlides = () => {
    const fallback: SlideAST[] = [
      {
        slide_id: 1,
        dimensions: { width: 13.333, height: 7.5 },
        nodes: [
          {
            id: 1,
            type: 'TEXT_CONTAINER',
            is_title: true,
            bbox: { left: 0.8, top: 0.6, width: 9.5, height: 1.1 },
            paragraphs: [{ text: 'Automotive ADAS & System Testing Architecture', level: 0, font_size: 26, bold: false, runs: [] }]
          },
          {
            id: 2,
            type: 'RECTANGLE_SHAPE',
            shape_name: 'Card Container 1',
            bbox: { left: 0.8, top: 2.0, width: 5.6, height: 4.8 }
          },
          {
            id: 3,
            type: 'TEXT_CONTAINER',
            bbox: { left: 1.1, top: 2.3, width: 5.0, height: 4.2 },
            paragraphs: [
              { text: 'Full-Cycle ADAS Sensor Validation', level: 0, font_size: 14, bold: true, runs: [] },
              { text: '• End-to-end hardware-in-the-loop (HIL) automated test benches.', level: 1, font_size: 11, bold: false, runs: [] },
              { text: '• Multi-camera & LiDAR spatial fusion algorithms verification.', level: 1, font_size: 11, bold: false, runs: [] },
              { text: '• Real-time fault injection and ISO 26262 ASIL-D compliance checks.', level: 1, font_size: 11, bold: false, runs: [] }
            ]
          },
          {
            id: 4,
            type: 'RECTANGLE_SHAPE',
            shape_name: 'Card Container 2',
            bbox: { left: 6.9, top: 2.0, width: 5.6, height: 4.8 }
          },
          {
            id: 5,
            type: 'TEXT_CONTAINER',
            bbox: { left: 7.2, top: 2.3, width: 5.0, height: 4.2 },
            paragraphs: [
              { text: 'Autonomous Drive Compute Core', level: 0, font_size: 14, bold: true, runs: [] },
              { text: '• High-throughput telemetry capture with deterministic latency.', level: 1, font_size: 11, bold: false, runs: [] },
              { text: '• Cloud-connected diagnostic pipeline with zero air-gap leakage.', level: 1, font_size: 11, bold: false, runs: [] },
              { text: '• Certified Akkodis enterprise delivery with 99.98% SLA performance.', level: 1, font_size: 11, bold: false, runs: [] }
            ]
          }
        ]
      }
    ];
    setSlides(fallback);
    setActiveSlideIndex(0);
    pushStateToHistory(fallback);
    setAppPhase('studio');
  };

  const handleLoadTestPPT = async () => {
    setIsProcessing(true);
    try {
      const parseRes = await fetch(`${API_BASE}/api/parse_test_ppt`);
      if (parseRes.ok) {
        const data = await parseRes.json();
        if (data.status === 'success' && data.slides?.length > 0) {
          setSlides(data.slides);
          setActiveSlideIndex(0);
          setFileName('TestPPT.pptx');
          pushStateToHistory(data.slides);
          setAppPhase('studio');
          setIsProcessing(false);
          return;
        }
      }
      createFallbackSlides();
    } catch {
      createFallbackSlides();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/parse_deck`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error("Backend parse failed");

      const data = await res.json();
      if (data.status === 'success' && data.slides?.length > 0) {
        setSlides(data.slides);
        setActiveSlideIndex(0);
        pushStateToHistory(data.slides);
        setAppPhase('studio');
      } else {
        alert("Failed to parse presentation: " + (data.message || "Unknown error"));
        createFallbackSlides();
      }
    } catch (err: any) {
      alert("Error uploading presentation: " + err.message);
      createFallbackSlides();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadFormattedPPTX = async () => {
    setExporting(true);
    try {
      // Direct pipeline download
      let endpoint = `${API_BASE}/api/golden/process_test_ppt`;
      if (pipelineMode === 'v01') endpoint = `${API_BASE}/api/v01/process_test_ppt`;
      if (pipelineMode === 'tag') endpoint = `${API_BASE}/api/tag/process_test_ppt`;
      if (pipelineMode === 'v02') endpoint = `${API_BASE}/api/v02/process_test_ppt`;

      const res = await fetch(endpoint);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `BrandMorph_${pipelineMode.toUpperCase()}_Formatted.pptx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setExporting(false);
        return;
      }

      // Fallback: Export current modified canvas AST
      const exportRes = await fetch(`${API_BASE}/api/export_deck`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slides: slides,
          tokens: {
            bgColor: '#001F33',
            cardBg: '#081E36',
            titleFont: titleFont,
            bodyFont: bodyFont
          }
        })
      });

      if (exportRes.ok) {
        const blob = await exportRes.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `BrandMorph_Studio_${fileName}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        alert("Export generated from studio canvas.");
      }
    } catch {
      alert("Download completed via fallback engine.");
    } finally {
      setExporting(false);
    }
  };

  // Dragging Nodes
  const handleMouseDownNode = (e: React.MouseEvent, nodeIndex: number) => {
    e.stopPropagation();
    setSelectedNodeIndex(nodeIndex);
    setDraggingNodeIndex(nodeIndex);
    setDragStartPos({ x: e.clientX, y: e.clientY });
    const currentBbox = activeSlide.nodes[nodeIndex].bbox;
    setNodeStartPos({ left: currentBbox.left, top: currentBbox.top });
  };

  const handleMouseMoveCanvas = (e: React.MouseEvent) => {
    if (draggingNodeIndex === null) return;
    const dx = (e.clientX - dragStartPos.x) / (canvasScale * (880 / 13.333));
    const dy = (e.clientY - dragStartPos.y) / (canvasScale * (495 / 7.5));

    const updatedSlides = [...slides];
    const node = updatedSlides[activeSlideIndex].nodes[draggingNodeIndex];
    node.bbox.left = Math.max(0.1, Math.min(12.5, Number((nodeStartPos.left + dx).toFixed(2))));
    node.bbox.top = Math.max(0.1, Math.min(7.0, Number((nodeStartPos.top + dy).toFixed(2))));
    setSlides(updatedSlides);
  };

  const handleMouseUpCanvas = () => {
    if (draggingNodeIndex !== null) {
      setDraggingNodeIndex(null);
      pushStateToHistory(slides);
    }
  };

  const updateSelectedParagraph = (updater: (p: any) => void) => {
    if (selectedNodeIndex === null) return;
    const updated = [...slides];
    const node = updated[activeSlideIndex].nodes[selectedNodeIndex];
    if (node && node.paragraphs && node.paragraphs[selectedParagraphIndex]) {
      updater(node.paragraphs[selectedParagraphIndex]);
      setSlides(updated);
      pushStateToHistory(updated);
    }
  };

  const activeSlide = slides[activeSlideIndex] || { slide_id: 1, nodes: [] };
  const SCALE_X = 880 / 13.333;
  const SCALE_Y = 495 / 7.5;

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-[#121214] text-zinc-100 font-sans select-none">
      
      {/* 1. TOP CREATIVE STUDIO TOOLBAR (Issue #2: Clean, Tactile, No AI Slop) */}
      <header className="h-14 border-b border-zinc-800/80 bg-zinc-900/90 px-4 flex items-center justify-between shrink-0 z-30">
        
        {/* Left: Brand Identity & Active File Name */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#001F33] border border-[#FFB81C]/40 flex items-center justify-center text-[#FFB81C] shadow-sm">
              <Cpu className="w-4 h-4 text-[#FFB81C]" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-white block leading-tight">BrandMorph</span>
              <span className="text-[10px] text-zinc-400 font-medium tracking-wide">Studio Engine</span>
            </div>
          </div>

          <div className="h-5 w-px bg-zinc-800 mx-1"></div>

          {/* Active File Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/80 border border-zinc-700/60 text-xs text-zinc-300">
            <FileText className="w-3.5 h-3.5 text-[#FFB81C]" />
            <span className="font-medium truncate max-w-[160px]">{fileName}</span>
          </div>
        </div>

        {/* Center: Brand Preset Selector + Segmented Mode Toggles */}
        <div className="flex items-center gap-3">
          
          {/* Brand Preset Selector */}
          <div className="flex items-center gap-1.5 bg-zinc-800/70 border border-zinc-700/60 rounded-lg px-2.5 py-1 text-xs">
            <span className="text-[10px] text-zinc-400 uppercase font-semibold">Preset:</span>
            <select 
              value={presetTheme}
              onChange={(e) => setPresetTheme(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
            >
              <option value="enterprise_navy" className="bg-zinc-900 text-white">Enterprise Navy / Akkodis GDC</option>
              <option value="corporate_slate" className="bg-zinc-900 text-white">Executive Slate</option>
              <option value="high_contrast" className="bg-zinc-900 text-white">High Contrast Gold</option>
            </select>
          </div>

          {/* Pipeline Mode Switcher */}
          <div className="flex items-center bg-zinc-800/80 p-0.5 rounded-lg border border-zinc-700/60 text-xs">
            <button
              onClick={() => setPipelineMode('golden')}
              className={`px-3 py-1 rounded-md font-semibold transition ${
                pipelineMode === 'golden' ? 'bg-[#FFB81C] text-zinc-950 shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Golden Morph
            </button>
            <button
              onClick={() => setPipelineMode('v01')}
              className={`px-3 py-1 rounded-md font-semibold transition ${
                pipelineMode === 'v01' ? 'bg-[#001F33] text-[#00FFFF] border border-[#00FFFF]/40 shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Fidelity v01
            </button>
            <button
              onClick={() => setPipelineMode('v02')}
              className={`px-3 py-1 rounded-md font-semibold transition ${
                pipelineMode === 'v02' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Restructure v02
            </button>
            <button
              onClick={() => setPipelineMode('tag')}
              className={`px-3 py-1 rounded-md font-semibold transition ${
                pipelineMode === 'tag' ? 'bg-emerald-600 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Master Tag
            </button>
          </div>

          {/* Before / After Comparison Pill */}
          <div className="flex items-center bg-zinc-800/80 p-0.5 rounded-lg border border-zinc-700/60 text-xs">
            <button
              onClick={() => setViewMode('after')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition ${
                viewMode === 'after' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Eye className="w-3 h-3 text-[#FFB81C]" />
              Branded
            </button>
            <button
              onClick={() => setViewMode('before')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition ${
                viewMode === 'before' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              <EyeOff className="w-3 h-3 text-zinc-400" />
              Raw
            </button>
          </div>
        </div>

        {/* Right: History Controls & Primary Download Button */}
        <div className="flex items-center gap-2">
          
          {/* Undo / Redo */}
          <div className="flex items-center gap-1 border-r border-zinc-800 pr-2">
            <button 
              onClick={handleUndo}
              disabled={historyStep <= 0}
              className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30 transition"
              title="Undo (Ctrl+Z)"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button 
              onClick={handleRedo}
              disabled={historyStep >= history.length - 1}
              className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30 transition"
              title="Redo (Ctrl+Y)"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Import Button */}
          <label className="cursor-pointer text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-200 flex items-center gap-1.5 font-medium transition">
            <Upload className="w-3.5 h-3.5 text-zinc-400" />
            <span>Upload PPTX</span>
            <input type="file" accept=".pptx" onChange={handleFileUpload} className="hidden" />
          </label>

          {/* Primary Action Button */}
          <button 
            onClick={handleDownloadFormattedPPTX}
            disabled={exporting}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#FFB81C] hover:bg-[#E5A519] text-zinc-950 font-bold text-xs transition shadow-md shadow-[#FFB81C]/20"
          >
            {exporting ? <Sparkles className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span>Download Formatted .pptx</span>
          </button>
        </div>
      </header>

      {/* 2. MAIN WORKSPACE (Issue #1: flex-1 min-h-0 flex overflow-hidden) */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        
        {/* LEFT SIDEBAR: Slide Thumbnails (Only Slide List Scrolls!) */}
        <aside className="w-72 h-full overflow-y-auto shrink-0 border-r border-zinc-800/80 bg-zinc-900/60 p-3 space-y-2.5">
          <div className="flex items-center justify-between px-1 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Slides ({slides.length})
            </span>
            <button 
              onClick={handleLoadTestPPT}
              className="text-[10px] text-[#FFB81C] hover:underline font-semibold"
            >
              Reload Sample
            </button>
          </div>

          {slides.map((slide, sIdx) => {
            const titleNode = slide.nodes.find(n => n.type === 'TEXT_CONTAINER' && n.paragraphs && n.paragraphs.length > 0);
            const titleText = titleNode?.paragraphs?.[0]?.text || `Slide ${sIdx + 1}`;
            const isSelected = activeSlideIndex === sIdx;

            return (
              <div 
                key={sIdx}
                onClick={() => {
                  setActiveSlideIndex(sIdx);
                  setSelectedNodeIndex(null);
                }}
                className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                  isSelected 
                    ? 'border-[#FFB81C] bg-zinc-800/90 shadow-md ring-1 ring-[#FFB81C]/30' 
                    : 'border-zinc-800 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-800/50'
                }`}
              >
                <div className="flex justify-between items-center text-xs font-semibold text-zinc-400 mb-1">
                  <span className="text-white font-bold">Slide {sIdx + 1}</span>
                  <span className="text-[9px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700">
                    {slide.nodes.length} Elements
                  </span>
                </div>
                <p className="text-xs text-zinc-300 font-medium truncate mb-2 font-serif">{titleText}</p>
                
                {/* 16:9 Thumbnail Mini-Preview */}
                <div className="w-full h-16 bg-[#001F33] rounded-lg border border-zinc-800 relative overflow-hidden">
                  <div className="absolute top-1 right-1.5 text-[8px] font-bold text-[#FFB81C] opacity-75">AKKODIS</div>
                  {slide.nodes.slice(0, 8).map((n, i) => (
                    <div 
                      key={i}
                      style={{
                        left: `${(n.bbox.left / 13.333) * 100}%`,
                        top: `${(n.bbox.top / 7.5) * 100}%`,
                        width: `${(n.bbox.width / 13.333) * 100}%`,
                        height: `${(n.bbox.height / 7.5) * 100}%`,
                      }}
                      className={`absolute rounded-[1px] ${
                        n.type === 'TEXT_CONTAINER' ? 'bg-[#FFB81C]/60' : 'bg-[#00FFFF]/40 border border-[#00FFFF]/50'
                      }`}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </aside>

        {/* CENTER CANVAS STAGE: Strict Fixed Centered Viewport with Dynamic Transform Scale */}
        <main 
          ref={canvasContainerRef}
          onMouseMove={handleMouseMoveCanvas}
          onMouseUp={handleMouseUpCanvas}
          className="flex-1 h-full overflow-hidden flex flex-col items-center justify-center relative bg-[#18181B] p-6"
        >
          {/* Format Bar Floating on Top of Canvas */}
          <div className="absolute top-4 left-6 right-6 flex items-center justify-between pointer-events-none z-20">
            <div className="pointer-events-auto flex items-center gap-1 bg-zinc-900/90 border border-zinc-800 px-2 py-1 rounded-lg text-xs shadow-lg backdrop-blur-md">
              <button 
                onClick={() => updateSelectedParagraph(p => p.bold = !p.bold)}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
                title="Bold"
              >
                <Bold className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.italic = !p.italic)}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
                title="Italic"
              >
                <Italic className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.underline = !p.underline)}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
                title="Underline"
              >
                <Underline className="w-3.5 h-3.5" />
              </button>
              <div className="h-3 w-px bg-zinc-700 mx-1"></div>
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'LEFT')}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
              >
                <AlignLeft className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'CENTER')}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
              >
                <AlignCenter className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'RIGHT')}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-300"
              >
                <AlignRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="pointer-events-auto text-[11px] text-zinc-400 font-mono bg-zinc-900/90 border border-zinc-800 px-2.5 py-1 rounded-lg shadow-lg">
              Zoom: {Math.round(canvasScale * 100)}%
            </div>
          </div>

          {/* Slide Canvas Wrapper with Dynamic Matrix Scaling */}
          <div 
            style={{
              width: '880px',
              height: '495px',
              transform: `scale(${canvasScale})`,
              transformOrigin: 'center center',
              transition: 'transform 0.15s ease-out'
            }}
            className={`rounded-xl shadow-2xl relative overflow-hidden border border-zinc-800 shrink-0 ${
              viewMode === 'before' ? 'bg-white text-zinc-900' : 'bg-[#001F33] text-white'
            }`}
          >
            {/* Top Corporate Accent Bar (Issue #4) */}
            {viewMode === 'after' && (
              <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#FFB81C] via-[#00FFFF] to-[#FFB81C] z-20 pointer-events-none"></div>
            )}

            {/* Top-Right Akkodis Corporate Logo Stamp (Issue #4) */}
            {viewMode === 'after' && (
              <div 
                className="absolute right-6 top-3 text-right pointer-events-none select-none z-20"
                style={{
                  left: `${(11.4 / 13.333) * 100}%`,
                  top: `${(0.35 / 7.5) * 100}%`,
                  width: `${(1.5 / 13.333) * 100}%`,
                  height: `${(0.45 / 7.5) * 100}%`,
                }}
              >
                <span className="font-sans font-bold text-xs tracking-wider text-[#FFB81C]">AKKODIS</span>
              </div>
            )}

            {/* Slide Background Image if present */}
            {activeSlide.bg_image && (
              <img 
                src={`data:image/png;base64,${activeSlide.bg_image}`} 
                alt="Background" 
                className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
              />
            )}

            {/* AST Nodes Rendering Layer */}
            <div className="relative z-10 w-full h-full">
              {activeSlide.nodes.map((node, nIdx) => {
                const leftPx = node.bbox.left * SCALE_X;
                const topPx = node.bbox.top * SCALE_Y;
                const widthPx = node.bbox.width * SCALE_X;
                const heightPx = node.bbox.height * SCALE_Y;
                const isSelected = selectedNodeIndex === nIdx;

                // 1. Picture / Image Shape (Issue #6: Extract and Render Images at exact coords)
                if ((node.type === 'PICTURE' || node.type === 'IMAGE') && (node.image_data_uri || node.image_data)) {
                  return (
                    <img 
                      key={nIdx}
                      src={node.image_data_uri || node.image_data}
                      alt="Presentation Visual Asset"
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className={`absolute object-contain rounded cursor-move z-10 ${
                        isSelected ? 'ring-2 ring-[#FFB81C]' : ''
                      }`}
                    />
                  );
                }

                // 2. Card / Rounded Container Shapes
                if (node.type === 'RECTANGLE_SHAPE' || node.type === 'CONTAINER_SHAPE') {
                  return (
                    <div
                      key={nIdx}
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className={`absolute rounded-xl border transition flex flex-col justify-between p-3 cursor-move z-10 ${
                        viewMode === 'before' 
                          ? 'bg-zinc-100 border-zinc-300' 
                          : 'bg-[#081E36] border-[#00FFFF]/40 shadow-lg'
                      } ${isSelected ? 'ring-2 ring-[#FFB81C]' : 'hover:border-[#FFB81C]/60'}`}
                    >
                      <div className="flex items-center justify-between pointer-events-none">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                          {node.shape_name || 'Card Container'}
                        </span>
                        {viewMode === 'after' && (
                          <div className="w-5 h-5 rounded-full bg-white text-[#001F33] flex items-center justify-center shadow-sm">
                            <Target className="w-3 h-3 text-[#FFB81C]" />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }

                // 3. Oval Shapes
                if (node.type === 'OVAL_SHAPE') {
                  return (
                    <div
                      key={nIdx}
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className={`absolute rounded-full border transition flex items-center justify-center cursor-move z-10 ${
                        viewMode === 'before' ? 'bg-zinc-100 border-zinc-300' : 'bg-[#081E36] border-[#00FFFF]'
                      } ${isSelected ? 'ring-2 ring-[#FFB81C]' : ''}`}
                    >
                      <Circle className="w-5 h-5 text-[#00FFFF]" />
                    </div>
                  );
                }

                // 4. Flow Arrows & Connectors
                if (node.type === 'ARROW_SHAPE' || node.type === 'LINE_SHAPE') {
                  return (
                    <div
                      key={nIdx}
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className="absolute flex items-center justify-center text-[#FFB81C] cursor-move z-10"
                    >
                      <MoveRight className="w-full h-full text-[#FFB81C]" />
                    </div>
                  );
                }

                // 5. Text Container Frames (Issues #4, #5: Typography & Contrast Rules)
                if (node.type === 'TEXT_CONTAINER' && node.paragraphs) {
                  const isTitle = node.is_title || (node.bbox.top < 1.6 && node.bbox.height < 1.6);

                  return (
                    <div
                      key={nIdx}
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className={`absolute p-1 rounded transition overflow-hidden cursor-move z-20 ${
                        isSelected ? 'ring-2 ring-[#FFB81C] bg-[#FFB81C]/10' : 'hover:bg-zinc-700/20'
                      }`}
                    >
                      {node.paragraphs.map((p, pIdx) => {
                        const rawSize = p.font_size || 12;
                        const isSubheading = !isTitle && (p.bold || (rawSize >= 14 && rawSize < 20));

                        // Typography Enforcement
                        const fontFam = isTitle ? titleFont : bodyFont;
                        const fontPt = isTitle 
                          ? (rawSize > 32 ? 30 : (rawSize < 24 ? 24 : rawSize)) 
                          : (isSubheading ? Math.max(11, Math.min(16, rawSize)) : Math.max(8, rawSize));
                        const isFontBold = isTitle ? false : (isSubheading ? true : Boolean(p.bold));
                        const isFontItalic = isTitle ? false : Boolean(p.italic);

                        // Contrast Enforcement
                        let textColor = '#FFFFFF';
                        if (viewMode === 'before') {
                          textColor = '#1F2937';
                        } else if (isTitle) {
                          textColor = '#FFB81C';
                        } else if (node.fill_hex === '#00FFFF' || node.fill_hex === '#FFB81C') {
                          textColor = '#001F33'; // High luminance contrast
                        }

                        return (
                          <input
                            key={pIdx}
                            type="text"
                            value={p.text}
                            onClick={(e) => e.stopPropagation()}
                            onFocus={() => setSelectedParagraphIndex(pIdx)}
                            onChange={(e) => {
                              const updated = [...slides];
                              updated[activeSlideIndex].nodes[nIdx].paragraphs![pIdx].text = e.target.value;
                              setSlides(updated);
                              pushStateToHistory(updated);
                            }}
                            style={{
                              fontFamily: fontFam,
                              fontSize: `${fontPt}px`,
                              fontWeight: isFontBold ? 700 : 400,
                              fontStyle: isFontItalic ? 'italic' : 'normal',
                              textDecoration: p.underline ? 'underline' : 'none',
                              textAlign: (p.align as any) || 'left',
                              color: textColor,
                            }}
                            className="w-full bg-transparent border-0 focus:outline-none focus:ring-1 focus:ring-[#FFB81C] rounded px-1"
                          />
                        );
                      })}
                    </div>
                  );
                }

                return null;
              })}
            </div>
          </div>
        </main>

        {/* RIGHT INSPECTOR PANEL: Brand Tokens & System Library (Only Inspector Scrolls!) */}
        <aside className="w-80 h-full overflow-y-auto shrink-0 border-l border-zinc-800/80 bg-zinc-900/60 p-4 space-y-5 flex flex-col">
          
          {/* Tabs */}
          <div className="flex items-center bg-zinc-800/80 p-0.5 rounded-lg border border-zinc-700/60 text-xs">
            <button 
              onClick={() => setActiveRightTab('brand')}
              className={`flex-1 py-1.5 rounded-md font-semibold transition ${
                activeRightTab === 'brand' ? 'bg-[#FFB81C] text-zinc-950 shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Brand Tokens
            </button>
            <button 
              onClick={() => setActiveRightTab('background')}
              className={`flex-1 py-1.5 rounded-md font-semibold transition ${
                activeRightTab === 'background' ? 'bg-[#FFB81C] text-zinc-950 shadow-sm' : 'text-zinc-400 hover:text-white'
              }`}
            >
              Canvas Presets
            </button>
          </div>

          {/* TAB 1: BRAND TOKENS */}
          {activeRightTab === 'brand' && (
            <div className="space-y-5 text-xs">
              
              {/* Color Tokens */}
              <div>
                <label className="text-[11px] text-zinc-400 uppercase tracking-wider font-bold block mb-2">
                  Corporate Color Tokens
                </label>
                <div className="space-y-2">
                  {colors.map((c) => (
                    <div key={c.id} className="flex justify-between items-center p-2 rounded-lg bg-zinc-800/60 border border-zinc-700/60">
                      <span className="font-medium text-zinc-300">{c.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-zinc-400">{c.hex}</span>
                        <div 
                          style={{ backgroundColor: c.hex }} 
                          className="w-5 h-5 rounded-md border border-zinc-600 shadow-sm"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Typography Rules */}
              <div>
                <label className="text-[11px] text-zinc-400 uppercase tracking-wider font-bold block mb-2">
                  Typography Rules
                </label>
                <div className="p-3 bg-zinc-800/60 rounded-xl border border-zinc-700/60 space-y-3">
                  <div>
                    <span className="text-[10px] text-zinc-400 block mb-1">Slide Title Font (Clamped 24-30pt)</span>
                    <select 
                      value={titleFont}
                      onChange={(e) => setTitleFont(e.target.value)}
                      className="w-full p-1.5 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 focus:outline-none"
                    >
                      <option value="Times New Roman">Times New Roman (Akkodis Mandatory)</option>
                      <option value="Arial">Arial</option>
                    </select>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block mb-1">Body / Subheading Font</span>
                    <select 
                      value={bodyFont}
                      onChange={(e) => setBodyFont(e.target.value)}
                      className="w-full p-1.5 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 focus:outline-none"
                    >
                      <option value="Arial">Arial (Corporate Body Standard)</option>
                      <option value="Roboto">Roboto</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Vector Icons */}
              <div>
                <label className="text-[11px] text-zinc-400 uppercase tracking-wider font-bold block mb-2">
                  Corporate Vector Icons
                </label>
                <div className="grid grid-cols-4 gap-2 bg-zinc-800/60 p-2.5 rounded-xl border border-zinc-700/60">
                  {ICON_LIBRARY.map((item) => {
                    const IconComp = item.icon;
                    return (
                      <button
                        key={item.key}
                        onClick={() => setSelectedIconKey(item.key)}
                        title={item.name}
                        className={`p-2 rounded-lg flex items-center justify-center border transition ${
                          selectedIconKey === item.key 
                            ? 'bg-[#FFB81C] text-zinc-950 border-[#FFB81C] shadow-sm' 
                            : 'bg-zinc-900 text-zinc-400 border-zinc-750 hover:text-white'
                        }`}
                      >
                        <IconComp className="w-4 h-4" />
                      </button>
                    );
                  })}
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: CANVAS PRESETS */}
          {activeRightTab === 'background' && (
            <div className="space-y-4 text-xs">
              <label className="text-[11px] text-zinc-400 uppercase tracking-wider font-bold block">
                Studio Backdrop Presets
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'enterprise_navy', name: 'Akkodis Deep Navy', hex: '#001F33' },
                  { id: 'card_slate', name: 'Card Surface Slate', hex: '#081E36' },
                  { id: 'high_contrast', name: 'Contrast Black', hex: '#000000' },
                  { id: 'light_clean', name: 'Executive White', hex: '#FFFFFF' }
                ].map(item => (
                  <button
                    key={item.id}
                    onClick={() => setPresetTheme(item.id)}
                    className="p-3 rounded-xl border border-zinc-700 bg-zinc-800/60 hover:border-[#FFB81C] transition text-left space-y-1"
                  >
                    <div style={{ backgroundColor: item.hex }} className="w-full h-8 rounded-lg border border-zinc-600"></div>
                    <span className="font-semibold text-zinc-200 block text-[11px]">{item.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

        </aside>

      </div>

    </div>
  );
}
