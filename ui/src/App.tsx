import React, { useState, useEffect, useRef } from 'react';
import { 
  Layers, Palette, Type, Grid, Image as ImageIcon, 
  RefreshCw, Download, Settings, ShieldCheck, Cpu,
  Upload, FileUp, Sparkles, Plus, Check, Trash2,
  Zap, Server, Target, ArrowRight, Monitor, ChevronRight,
  Maximize2, Move, Copy, Sliders, Eye, Globe, Database, Lock,
  Activity, Cloud, Award, Share2, FileJson, Sun, Moon, Laptop,
  Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight, AlignJustify,
  Indent, Outdent, ChevronDown, MoveRight, LayoutTemplate, PlusCircle,
  RotateCcw, RotateCw, Circle, Square, Minus
} from 'lucide-react';

interface ASTNode {
  id: number;
  type: string;
  shape_name?: string;
  bbox: { left: number; top: number; width: number; height: number };
  image_data?: string;
  paragraphs?: { 
    text: string; 
    level: number; 
    font_size?: number;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    align?: string;
    runs: any[] 
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

export default function StudioWorkspace() {
  const [appPhase, setAppPhase] = useState<'splash' | 'import' | 'studio'>('splash');
  const [slides, setSlides] = useState<SlideAST[]>([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileName, setFileName] = useState<string>('TestPPT.pptx');
  const [exporting, setExporting] = useState(false);

  // Undo / Redo History Stack
  const [history, setHistory] = useState<SlideAST[][]>([]);
  const [historyStep, setHistoryStep] = useState<number>(-1);

  // Right Panel Active Tab: 'background' | 'brand'
  const [activeRightTab, setActiveRightTab] = useState<'background' | 'brand'>('background');

  // Selection & Formatting state
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number | null>(null);
  const [selectedParagraphIndex, setSelectedParagraphIndex] = useState<number>(0);

  // Canvas Background Style Preset ('dark' | 'white' | 'blueGradient' | 'slate')
  const [bgStyle, setBgStyle] = useState<string>('dark'); 

  // Dragging Node state
  const [draggingNodeIndex, setDraggingNodeIndex] = useState<number | null>(null);
  const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [nodeStartPos, setNodeStartPos] = useState<{ left: number; top: number }>({ left: 0, top: 0 });

  // Icon Swap state
  const [selectedIconKey, setSelectedIconKey] = useState<string>('zap');

  // Akkodis Color Tokens
  const [colors, setColors] = useState<ColorToken[]>([
    { id: 'gold', name: 'Gold Text 2', hex: '#FFB81C' },
    { id: 'aqua', name: 'Aqua Background 2', hex: '#00FFFF' },
    { id: 'darkBg', name: 'Dark Blue Base', hex: '#030C1E' },
    { id: 'cardBg', name: 'Card Surface Slate', hex: '#081632' },
    { id: 'white', name: 'High Contrast White', hex: '#FFFFFF' },
    { id: 'darkBlue', name: 'Dark Blue Accent', hex: '#0C3264' },
  ]);

  const [newColorName, setNewColorName] = useState('');
  const [newColorHex, setNewColorHex] = useState('#FFB81C');
  const [showAddColor, setShowAddColor] = useState(false);

  // Typography System
  const [titleFont, setTitleFont] = useState('Times New Roman');
  const [bodyFont, setBodyFont] = useState('Arial');

  // Icon Catalog
  const ICON_LIBRARY = [
    { key: 'zap', name: 'Zap / Energy', icon: Zap },
    { key: 'server', name: 'Server / Node', icon: Server },
    { key: 'shield', name: 'Shield / Security', icon: ShieldCheck },
    { key: 'target', name: 'Target / Goal', icon: Target },
    { key: 'cpu', name: 'CPU / Processing', icon: Cpu },
    { key: 'layers', name: 'Layers / Stack', icon: Layers },
    { key: 'monitor', name: 'Monitor / Display', icon: Monitor },
    { key: 'globe', name: 'Globe / Network', icon: Globe },
    { key: 'database', name: 'Database / Storage', icon: Database },
    { key: 'lock', name: 'Lock / Compliance', icon: Lock },
    { key: 'activity', name: 'Activity / SLA', icon: Activity },
    { key: 'cloud', name: 'Cloud / Infrastructure', icon: Cloud },
    { key: 'award', name: 'Award / Quality', icon: Award },
    { key: 'sparkles', name: 'AI / Optimization', icon: Sparkles }
  ];

  // Auto transition splash to import
  useEffect(() => {
    if (appPhase === 'splash') {
      const timer = setTimeout(() => setAppPhase('import'), 1400);
      return () => clearTimeout(timer);
    }
  }, [appPhase]);

  // Push state into Undo/Redo history
  const pushStateToHistory = (newSlides: SlideAST[]) => {
    const newHistory = history.slice(0, historyStep + 1);
    newHistory.push(JSON.parse(JSON.stringify(newSlides)));
    setHistory(newHistory);
    setHistoryStep(newHistory.length - 1);
  };

  const undo = () => {
    if (historyStep > 0) {
      const prevStep = historyStep - 1;
      setSlides(JSON.parse(JSON.stringify(history[prevStep])));
      setHistoryStep(prevStep);
    }
  };

  const redo = () => {
    if (historyStep < history.length - 1) {
      const nextStep = historyStep + 1;
      setSlides(JSON.parse(JSON.stringify(history[nextStep])));
      setHistoryStep(nextStep);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        if (e.shiftKey) redo();
        else undo();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        redo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [historyStep, history]);

  // Load TestPPT.pptx
  const loadTestPPT = async () => {
    setIsProcessing(true);
    try {
      const res = await fetch('http://localhost:8000/api/parse_test_ppt');
      const data = await res.json();
      if (data.status === 'success' && data.slides.length > 0) {
        setSlides(data.slides);
        setActiveSlideIndex(0);
        setFileName('TestPPT.pptx');
        pushStateToHistory(data.slides);
        setAppPhase('studio');
      } else {
        createFallbackSlides();
      }
    } catch (err) {
      createFallbackSlides();
    } finally {
      setIsProcessing(false);
    }
  };

  const createFallbackSlides = () => {
    const fallback: SlideAST[] = Array.from({ length: 4 }).map((_, idx) => ({
      slide_id: idx + 1,
      dimensions: { width: 13.333, height: 7.5 },
      nodes: [
        {
          id: 1,
          type: 'TEXT_CONTAINER',
          bbox: { left: 1.0, top: 0.8, width: 11.3, height: 1.0 },
          paragraphs: [
            { text: idx === 0 ? 'Capacity Management & SLA Performance' : `Parsed Slide ${idx + 1}`, level: 0, font_size: 24, bold: true, align: 'LEFT', runs: [] }
          ]
        },
        {
          id: 2,
          type: 'RECTANGLE_SHAPE',
          bbox: { left: 1.0, top: 2.0, width: 3.5, height: 4.5 }
        },
        {
          id: 3,
          type: 'TEXT_CONTAINER',
          bbox: { left: 1.2, top: 2.2, width: 3.1, height: 4.0 },
          paragraphs: [
            { text: 'High Capacity Node', level: 0, font_size: 14, bold: true, runs: [] },
            { text: 'Node stability running at optimum threshold under 12ms latency.', level: 1, font_size: 11, runs: [] }
          ]
        },
        {
          id: 4,
          type: 'ARROW_SHAPE',
          bbox: { left: 4.6, top: 4.0, width: 0.6, height: 0.4 }
        },
        {
          id: 5,
          type: 'RECTANGLE_SHAPE',
          bbox: { left: 5.3, top: 2.0, width: 3.5, height: 4.5 }
        },
        {
          id: 6,
          type: 'TEXT_CONTAINER',
          bbox: { left: 5.5, top: 2.2, width: 3.1, height: 4.0 },
          paragraphs: [
            { text: 'Medium Capacity Node', level: 0, font_size: 14, bold: true, runs: [] },
            { text: 'Resource allocation approaching 78% limit. Rebalancing scheduled.', level: 1, font_size: 11, runs: [] }
          ]
        }
      ]
    }));
    setSlides(fallback);
    setActiveSlideIndex(0);
    setFileName('TestPPT.pptx');
    pushStateToHistory(fallback);
    setAppPhase('studio');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      setIsProcessing(true);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('http://localhost:8000/api/parse_deck', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.status === 'success' && data.slides.length > 0) {
          setSlides(data.slides);
          setActiveSlideIndex(0);
          pushStateToHistory(data.slides);
          setAppPhase('studio');
        } else {
          alert("Error parsing presentation: " + (data.message || "Unknown error"));
        }
      } catch (err) {
        loadTestPPT();
      } finally {
        setIsProcessing(false);
      }
    }
  };

  // Export Native PPTX
  const handleExportPPTX = async () => {
    setExporting(true);
    try {
      const bgHexMap: Record<string, string> = {
        dark: '#030C1E',
        white: '#FFFFFF',
        blueGradient: '#0EA5E9',
        slate: '#F1F5F9'
      };

      const payload = {
        slides: slides,
        tokens: {
          bgColor: bgHexMap[bgStyle] || '#030C1E',
          cardBg: bgStyle === 'white' ? '#FFFFFF' : '#081632',
          titleFont: titleFont,
          bodyFont: bodyFont
        }
      };

      const res = await fetch('http://localhost:8000/api/export_deck', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanName = fileName.replace(/\s*\(\d+\s*slides\)/i, '');
        a.download = `Reskinned_${cleanName.endsWith('.pptx') ? cleanName : cleanName + '.pptx'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        alert("Failed to export native PPTX deck.");
      }
    } catch (err) {
      alert("Error exporting deck: " + err);
    } finally {
      setExporting(false);
    }
  };

  // Node Dragging Handler Setup
  const handleMouseDownNode = (e: React.MouseEvent, nIdx: number) => {
    e.stopPropagation();
    setSelectedNodeIndex(nIdx);
    setDraggingNodeIndex(nIdx);
    setDragStartPos({ x: e.clientX, y: e.clientY });

    const node = slides[activeSlideIndex]?.nodes[nIdx];
    if (node) {
      setNodeStartPos({ left: node.bbox.left, top: node.bbox.top });
    }
  };

  const handleMouseMoveCanvas = (e: React.MouseEvent) => {
    if (draggingNodeIndex !== null) {
      const deltaXInches = (e.clientX - dragStartPos.x) / SCALE_X;
      const deltaYInches = (e.clientY - dragStartPos.y) / SCALE_Y;

      const updated = [...slides];
      const node = updated[activeSlideIndex]?.nodes[draggingNodeIndex];
      if (node) {
        node.bbox.left = Math.max(0, Math.min(12.5, Number((nodeStartPos.left + deltaXInches).toFixed(3))));
        node.bbox.top = Math.max(0, Math.min(6.8, Number((nodeStartPos.top + deltaYInches).toFixed(3))));
        setSlides(updated);
      }
    }
  };

  const handleMouseUpCanvas = () => {
    if (draggingNodeIndex !== null) {
      setDraggingNodeIndex(null);
      pushStateToHistory(slides);
    }
  };

  const updateSelectedParagraph = (updateFn: (p: any) => void) => {
    if (selectedNodeIndex === null) return;
    const updatedSlides = [...slides];
    const node = updatedSlides[activeSlideIndex]?.nodes[selectedNodeIndex];
    if (node && node.paragraphs && node.paragraphs[selectedParagraphIndex]) {
      updateFn(node.paragraphs[selectedParagraphIndex]);
      setSlides(updatedSlides);
      pushStateToHistory(updatedSlides);
    }
  };

  const renderVectorIcon = (key: string, className: string = "w-5 h-5") => {
    const match = ICON_LIBRARY.find(i => i.key === key) || ICON_LIBRARY[0];
    const IconComp = match.icon;
    return <IconComp className={className} />;
  };

  // Adaptive Styling Rules
  const isDarkCanvas = bgStyle === 'dark' || bgStyle === 'slate';

  const getCanvasBgClass = () => {
    switch (bgStyle) {
      case 'white': return 'bg-white border-slate-300';
      case 'blueGradient': return 'bg-gradient-to-br from-blue-50 via-white to-sky-50 border-blue-200';
      case 'slate': return 'bg-[#0F172A] border-slate-800';
      default: return 'bg-[#030C1E] border-slate-800';
    }
  };

  const getTitleColorClass = () => {
    return isDarkCanvas ? 'text-[#FFB81C]' : 'text-[#0F172A]';
  };

  const getBodyTextColorClass = () => {
    return isDarkCanvas ? 'text-white' : 'text-slate-700';
  };

  const getCardBgClass = () => {
    return isDarkCanvas ? 'bg-[#081632] border-cyan-400' : 'bg-white border-blue-600';
  };

  const activeSlide = slides[activeSlideIndex] || { slide_id: 1, nodes: [] };

  const SCALE_X = 880 / 13.333;
  const SCALE_Y = 495 / 7.5;

  // 1. SPLASH SCREEN
  if (appPhase === 'splash') {
    return (
      <div className="h-screen w-screen bg-[#030C1E] flex flex-col items-center justify-center text-white relative overflow-hidden select-none">
        <div className="z-10 flex flex-col items-center space-y-6 animate-fade-in">
          <div className="w-20 h-20 rounded-2xl bg-blue-600 flex items-center justify-center shadow-2xl shadow-blue-500/50 transform animate-bounce">
            <Cpu className="w-10 h-10 text-white" />
          </div>
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-extrabold tracking-tight text-white">BrandMorph Engine</h1>
            <p className="text-sm text-amber-400 font-semibold tracking-wide">Akkodis Presentation AST Architecture</p>
          </div>
        </div>
      </div>
    );
  }

  // 2. RESOURCE IMPORT STAGE
  if (appPhase === 'import') {
    return (
      <div className="h-screen w-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-slate-800 font-sans select-none">
        <div className="max-w-xl w-full bg-white rounded-2xl border border-slate-200 shadow-xl p-8 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-600/30">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">BrandMorph Studio</h2>
              <p className="text-xs text-slate-500">Import PPTX deck or load sample presentation</p>
            </div>
          </div>

          <div className="border-2 border-dashed border-blue-200 hover:border-blue-500 bg-blue-50/40 hover:bg-blue-50 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition text-center relative overflow-hidden">
            <input 
              type="file" 
              accept=".pptx,.ppt"
              onChange={handleFileUpload}
              className="absolute inset-0 opacity-0 cursor-pointer z-10"
            />
            <div className="w-14 h-14 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-3 shadow-inner">
              <FileUp className="w-7 h-7" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Click to browse PowerPoint deck (.pptx)
            </p>
            <p className="text-xs text-slate-500 mt-1">Automatic AST Decompiler parses layout, shapes & text frames</p>
          </div>

          {isProcessing && (
            <div className="flex items-center justify-center gap-3 p-4 bg-blue-50 text-blue-700 rounded-lg text-xs font-semibold border border-blue-200">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Decompiling PowerPoint AST and applying Akkodis Brand Rules...
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button 
              onClick={loadTestPPT}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-md shadow-blue-600/20"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              Load Sample Deck (TestPPT.pptx)
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3. MAIN STUDIO WORKSPACE (Clean White UI Shell Reset)
  return (
    <div className="flex h-screen w-screen bg-slate-100 text-slate-800 font-sans overflow-hidden select-none">
      
      {/* LEFT PANEL: SLIDE NAVIGATOR */}
      <div className="w-72 bg-white border-r border-slate-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-600/30">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-sm text-slate-900 block leading-tight">BrandMorph</span>
              <span className="text-[10px] text-blue-600 font-medium tracking-wide uppercase">Engine Studio</span>
            </div>
          </div>
          <button 
            onClick={() => setAppPhase('import')}
            className="text-[11px] px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 flex items-center gap-1 font-medium transition"
          >
            <Upload className="w-3 h-3" />
            Import
          </button>
        </div>

        {/* Slide List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-slate-50/50">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Slides ({slides.length})
            </span>
          </div>

          {slides.map((slide, sIdx) => {
            const titleNode = slide.nodes.find(n => n.type === 'TEXT_CONTAINER' && n.paragraphs && n.paragraphs.length > 0);
            const titleText = titleNode?.paragraphs?.[0]?.text || `Slide ${sIdx + 1}`;

            return (
              <div 
                key={sIdx}
                onClick={() => {
                  setActiveSlideIndex(sIdx);
                  setSelectedNodeIndex(null);
                }}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  activeSlideIndex === sIdx 
                    ? 'border-blue-600 bg-white shadow-md ring-2 ring-blue-500/20' 
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                }`}
              >
                <div className="flex justify-between items-center text-xs font-semibold text-slate-500 mb-1">
                  <span className="text-slate-800 font-bold">Slide {sIdx + 1}</span>
                  <span className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-medium border border-blue-100 truncate max-w-[100px]">
                    AST {slide.nodes.length} Nodes
                  </span>
                </div>
                <p className="text-xs text-slate-800 font-medium truncate mb-2 font-serif">{titleText}</p>
                
                {/* Mini Preview */}
                <div className="w-full h-16 bg-[#030C1E] rounded-lg border border-slate-200 relative overflow-hidden">
                  {slide.nodes.slice(0, 6).map((n, i) => (
                    <div 
                      key={i}
                      style={{
                        left: `${(n.bbox.left / 13.333) * 100}%`,
                        top: `${(n.bbox.top / 7.5) * 100}%`,
                        width: `${(n.bbox.width / 13.333) * 100}%`,
                        height: `${(n.bbox.height / 7.5) * 100}%`,
                      }}
                      className={`absolute rounded-[1px] ${
                        n.type === 'TEXT_CONTAINER' ? 'bg-amber-400/60' : 'bg-cyan-500/40 border border-cyan-400'
                      }`}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* CENTER PANEL: CANVAS & FORMATTING TOOLBAR */}
      <div className="flex-1 flex flex-col bg-slate-100">
        
        {/* Top Control Bar */}
        <div className="h-14 border-b border-slate-200 flex items-center justify-between px-6 bg-white shadow-sm">
          
          {/* Formatting & Undo/Redo */}
          <div className="flex items-center gap-2">
            
            {/* Undo / Redo */}
            <div className="flex items-center gap-1 border-r border-slate-200 pr-3">
              <button 
                onClick={undo}
                disabled={historyStep <= 0}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700 disabled:opacity-30 border border-slate-200"
                title="Undo (Ctrl+Z)"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={redo}
                disabled={historyStep >= history.length - 1}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700 disabled:opacity-30 border border-slate-200"
                title="Redo (Ctrl+Y)"
              >
                <RotateCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Font Formatting */}
            <div className="flex items-center gap-1 border-r border-slate-200 pr-3">
              <button 
                onClick={() => updateSelectedParagraph(p => p.bold = !p.bold)}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700 border border-slate-200"
                title="Bold"
              >
                <Bold className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.italic = !p.italic)}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700 border border-slate-200"
                title="Italic"
              >
                <Italic className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.underline = !p.underline)}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700 border border-slate-200"
                title="Underline"
              >
                <Underline className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Font Size Adjuster */}
            <div className="flex items-center gap-1 border-r border-slate-200 pr-3">
              <button 
                onClick={() => updateSelectedParagraph(p => p.font_size = Math.max(8, (p.font_size || 12) - 1))}
                className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-xs font-bold border border-slate-200 text-slate-800"
                title="Decrease Font Size"
              >
                A-
              </button>
              <span className="text-xs font-bold text-blue-600 px-1">
                {selectedNodeIndex !== null && activeSlide.nodes[selectedNodeIndex]?.paragraphs?.[0]?.font_size || 12}pt
              </span>
              <button 
                onClick={() => updateSelectedParagraph(p => p.font_size = Math.min(48, (p.font_size || 12) + 1))}
                className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-xs font-bold border border-slate-200 text-slate-800"
                title="Increase Font Size"
              >
                A+
              </button>
            </div>

            {/* Alignments */}
            <div className="flex items-center gap-1">
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'LEFT')}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700"
                title="Align Left"
              >
                <AlignLeft className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'CENTER')}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700"
                title="Align Center"
              >
                <AlignCenter className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => updateSelectedParagraph(p => p.align = 'RIGHT')}
                className="p-1.5 rounded hover:bg-slate-100 text-slate-700"
                title="Align Right"
              >
                <AlignRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Export Action */}
          <div className="flex items-center gap-3">
            <button 
              onClick={handleExportPPTX}
              disabled={exporting}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-md shadow-blue-600/20"
            >
              {exporting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              Export Native PPTX
            </button>
          </div>
        </div>

        {/* SPATIAL CANVAS VIEWPORT (WITH DRAGGABLE MOVEABLE NODES) */}
        <div 
          onMouseMove={handleMouseMoveCanvas}
          onMouseUp={handleMouseUpCanvas}
          className="flex-1 p-6 flex items-center justify-center overflow-auto relative"
        >
          <div 
            className={`w-[880px] h-[495px] ${getCanvasBgClass()} rounded-xl shadow-xl relative overflow-hidden transition-all border`}
          >
            {/* Non-Selectable Background Layer (Locked at z-index: 0) */}
            {activeSlide.bg_image ? (
              <img 
                src={`data:image/png;base64,${activeSlide.bg_image}`} 
                alt="Slide Background Master" 
                className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
              />
            ) : (
              <div className="absolute inset-0 pointer-events-none z-0 opacity-15 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]"></div>
            )}

            {/* Render Freeform Moveable AST Nodes (Z-Index: 10 above Background) */}
            <div className="relative z-10 w-full h-full">
              {activeSlide.nodes.map((node, nIdx) => {
                const leftPx = node.bbox.left * SCALE_X;
                const topPx = node.bbox.top * SCALE_Y;
                const widthPx = node.bbox.width * SCALE_X;
                const heightPx = node.bbox.height * SCALE_Y;

                const isSelected = selectedNodeIndex === nIdx;

                // 1. Raw Rectangle / Rounded Container Shapes
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
                      className={`absolute rounded-xl border-2 ${getCardBgClass()} shadow-md transition flex flex-col justify-between p-3 cursor-move ${
                        isSelected ? 'ring-2 ring-amber-400 shadow-lg' : 'hover:border-cyan-300'
                      }`}
                    >
                      <div className="flex items-center justify-between pointer-events-none">
                        <span className="text-[10px] font-bold uppercase tracking-wide opacity-80">{node.shape_name || 'Rectangle Container'}</span>
                        <div className="w-5 h-5 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200">
                          {renderVectorIcon(selectedIconKey, "w-3 h-3")}
                        </div>
                      </div>
                    </div>
                  );
                }

                // 2. Raw Oval / Circle Shapes
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
                      className={`absolute rounded-full border-2 ${getCardBgClass()} shadow-md transition flex items-center justify-center cursor-move ${
                        isSelected ? 'ring-2 ring-amber-400' : 'hover:border-cyan-300'
                      }`}
                    >
                      <Circle className="w-5 h-5 text-cyan-400" />
                    </div>
                  );
                }

                // 3. Raw Arrows & Flow Shapes
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
                      className="absolute flex items-center justify-center text-amber-400 cursor-move"
                    >
                      <MoveRight className="w-full h-full text-amber-400" />
                    </div>
                  );
                }

                // 4. Raw Image Shapes
                if (node.type === 'IMAGE' && node.image_data) {
                  return (
                    <img 
                      key={nIdx}
                      src={node.image_data}
                      alt="Slide Shape Image"
                      onMouseDown={(e) => handleMouseDownNode(e, nIdx)}
                      style={{
                        left: `${leftPx}px`,
                        top: `${topPx}px`,
                        width: `${widthPx}px`,
                        height: `${heightPx}px`,
                      }}
                      className={`absolute object-contain rounded cursor-move ${
                        isSelected ? 'ring-2 ring-blue-500' : ''
                      }`}
                    />
                  );
                }

                // 5. Text Container Frames (Fixed Selection Highlighting Bug)
                if (node.type === 'TEXT_CONTAINER' && node.paragraphs) {
                  const isTitle = node.bbox.top < 1.5;

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
                      className={`absolute p-1 rounded transition overflow-hidden cursor-move ${
                        isSelected ? 'ring-2 ring-blue-500 bg-blue-500/10' : 'hover:bg-slate-200/20'
                      }`}
                    >
                      {node.paragraphs.map((p, pIdx) => (
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
                            fontFamily: isTitle ? titleFont : bodyFont,
                            fontSize: isTitle ? '24px' : (p.font_size ? `${p.font_size}px` : '11px'),
                            fontWeight: p.bold ? 'bold' : (isTitle ? 'bold' : 'normal'),
                            fontStyle: p.italic ? 'italic' : 'normal',
                            textDecoration: p.underline ? 'underline' : 'none',
                            textAlign: (p.align as any) || 'left',
                          }}
                          className={`w-full bg-transparent border-0 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded px-1 text-inherit ${
                            isTitle ? getTitleColorClass() + ' font-serif font-bold' : getBodyTextColorClass() + ' font-sans'
                          }`}
                        />
                      ))}
                    </div>
                  );
                }

                return null;
              })}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: RE-ORDERED BRAND SYSTEM & BACKGROUND LIBRARY */}
      <div className="w-80 bg-white border-l border-slate-200 flex flex-col shadow-sm">
        
        {/* Navigation Tabs */}
        <div className="p-2 border-b border-slate-200 flex items-center gap-1 bg-white">
          <button 
            onClick={() => setActiveRightTab('background')}
            className={`flex-1 text-xs py-2 rounded-lg font-semibold transition flex items-center justify-center gap-1.5 ${
              activeRightTab === 'background' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            Background Library
          </button>
          <button 
            onClick={() => setActiveRightTab('brand')}
            className={`flex-1 text-xs py-2 rounded-lg font-semibold transition flex items-center justify-center gap-1.5 ${
              activeRightTab === 'brand' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            Brand Tokens
          </button>
        </div>

        {/* TAB 1: BACKGROUND STYLE & EXTRACTED DECK LIBRARY */}
        {activeRightTab === 'background' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Background Canvas Presets
            </div>

            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'dark', name: 'Akkodis Dark Base' },
                { id: 'white', name: 'Pure White' },
                { id: 'blueGradient', name: 'Sky Gradient' },
                { id: 'slate', name: 'Corporate Slate' }
              ].map(preset => (
                <button
                  key={preset.id}
                  onClick={() => setBgStyle(preset.id)}
                  className={`p-2.5 rounded-lg text-xs font-semibold border transition text-center ${
                    bgStyle === preset.id ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-sm' : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  {preset.name}
                </button>
              ))}
            </div>

            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 pt-3">
              Extracted Slide Backgrounds ({slides.filter(s => s.bg_image).length})
            </div>

            <div className="space-y-2">
              {slides.map((s, idx) => {
                if (!s.bg_image) return null;
                return (
                  <div 
                    key={idx}
                    onClick={() => {
                      const updated = [...slides];
                      updated[activeSlideIndex].bg_image = s.bg_image;
                      setSlides(updated);
                      pushStateToHistory(updated);
                    }}
                    className="p-2 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer hover:border-blue-500 transition flex items-center gap-3"
                  >
                    <img 
                      src={`data:image/png;base64,${s.bg_image}`} 
                      alt={`Slide ${s.slide_id} Background`} 
                      className="w-16 h-10 rounded object-cover border border-slate-300"
                    />
                    <div>
                      <span className="text-xs font-bold text-slate-800 block">Slide {s.slide_id} Background</span>
                      <span className="text-[10px] text-blue-600 font-semibold">Apply to Active Slide</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: BRAND SYSTEM TOKENS */}
        {activeRightTab === 'brand' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            
            {/* COLOR TOKENS */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-[11px] text-slate-500 uppercase tracking-wider font-bold">
                  Brand Color Tokens
                </label>
              </div>

              <div className="space-y-2">
                {colors.map((c) => (
                  <div key={c.id} className="flex justify-between items-center p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-xs font-medium text-slate-700">{c.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-slate-500">{c.hex}</span>
                      <input 
                        type="color" 
                        value={c.hex}
                        onChange={(e) => setColors(colors.map(col => col.id === c.id ? { ...col, hex: e.target.value } : col))}
                        className="w-5 h-5 rounded cursor-pointer border-0"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* TYPOGRAPHY SYSTEM */}
            <div>
              <label className="text-[11px] text-slate-500 uppercase tracking-wider font-bold block mb-2">
                Typography System
              </label>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                <div>
                  <div className="text-[10px] text-slate-500 mb-1 font-semibold">Title Font Family</div>
                  <select 
                    value={titleFont}
                    onChange={(e) => setTitleFont(e.target.value)}
                    className="w-full text-xs p-1.5 bg-white border border-slate-300 rounded focus:outline-none"
                  >
                    <option value="Times New Roman">Times New Roman (Akkodis Token Rule)</option>
                    <option value="Arial">Arial</option>
                  </select>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 mb-1 font-semibold">Body Copy Font Family</div>
                  <select 
                    value={bodyFont}
                    onChange={(e) => setBodyFont(e.target.value)}
                    className="w-full text-xs p-1.5 bg-white border border-slate-300 rounded focus:outline-none"
                  >
                    <option value="Arial">Arial (Akkodis Token Rule)</option>
                    <option value="Roboto">Roboto</option>
                    <option value="Times New Roman">Times New Roman</option>
                  </select>
                </div>
              </div>
            </div>

            {/* VECTOR ICON LIBRARY */}
            <div>
              <label className="text-[11px] text-slate-500 uppercase tracking-wider font-bold block mb-2">
                Vector Icon Component Library
              </label>
              <div className="grid grid-cols-4 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                {ICON_LIBRARY.map((item) => {
                  const IconComp = item.icon;
                  return (
                    <button
                      key={item.key}
                      onClick={() => setSelectedIconKey(item.key)}
                      title={item.name}
                      className={`p-2.5 rounded-lg flex items-center justify-center border transition ${
                        selectedIconKey === item.key ? 'bg-blue-600 text-white border-blue-600 shadow-md' : 'bg-white text-slate-600 border-slate-200 hover:border-blue-400'
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

      </div>

    </div>
  );
}
