import collections
import collections.abc
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

# Initialize presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Theme Colors
BG_COLOR = RGBColor(3, 12, 30)          # Very dark navy blue
CARD_BG = RGBColor(8, 22, 50)           # Deep slate blue card background
BORDER_BLUE = RGBColor(12, 50, 100)      # Subtle blue borders
CYAN = RGBColor(0, 255, 255)            # Cyan (#00FFFF)
GOLD = RGBColor(255, 184, 28)           # Gold (#FFB81C)
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(0, 0, 0)
RED_BORDER = RGBColor(220, 30, 40)      # Alert red border
RED_BG = RGBColor(40, 15, 25)
GREEN_BORDER = RGBColor(40, 180, 70)    # Success green border
GREEN_BG = RGBColor(15, 40, 25)
TEXT_MUTED = RGBColor(160, 180, 200)

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_slide_title(slide, text):
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.33), Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = "Times New Roman"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 1 GENERATION
# ==========================================
def build_slide_1():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_slide_title(slide, "KPI PERFORMANCE RECOVERY & RESKILLING FRAMEWORK")
    
    # --- 1. KPI TRIGGERS SECTION ---
    # Chevron tag
    chev1 = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.4), Inches(0.9), Inches(2.2), Inches(0.35))
    chev1.fill.solid()
    chev1.fill.fore_color.rgb = RGBColor(12, 60, 130)
    chev1.line.fill.background()
    p_chev1 = chev1.text_frame.paragraphs[0]
    p_chev1.text = "  1   KPI TRIGGERS"
    p_chev1.font.bold = True
    p_chev1.font.size = Pt(11)
    p_chev1.font.color.rgb = CYAN
    p_chev1.font.name = "Arial"
    
    # 3 Trigger Cards
    card_w = Inches(3.6)
    card_h = Inches(1.1)
    card_y = Inches(1.35)
    
    triggers = [
        ("OTD < 95%", "On Time Delivery", "🚚", 0.4),
        ("FTR < 95%", "First Time Resolution", "✔️", 4.4),
        ("CSAT < 7/10", "Customer Satisfaction", "😊", 8.4)
    ]
    
    for title, subtitle, icon, x in triggers:
        # Red-bordered card
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(card_y), card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = RED_BG
        card.line.color.rgb = RED_BORDER
        card.line.width = Pt(1.5)
        
        # Circle icon
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.25), Inches(card_y + 0.2), Inches(0.7), Inches(0.7))
        circ.fill.solid()
        circ.fill.fore_color.rgb = WHITE
        circ.line.fill.background()
        p_circ = circ.text_frame.paragraphs[0]
        p_circ.text = icon
        p_circ.font.size = Pt(22)
        p_circ.alignment = PP_ALIGN.CENTER
        
        # Text box
        tb = slide.shapes.add_textbox(Inches(x + 1.1), Inches(card_y + 0.15), Inches(2.2), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = WHITE
        p1.font.name = "Roboto"
        
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(10)
        p2.font.color.rgb = TEXT_MUTED
        p2.font.name = "Arial"
        
        # Exclamation badge
        badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + card_w - 0.45), Inches(card_y + 0.1), Inches(0.35), Inches(0.35))
        badge.fill.solid()
        badge.fill.fore_color.rgb = RED_BORDER
        badge.line.fill.background()
        p_badge = badge.text_frame.paragraphs[0]
        p_badge.text = "!"
        p_badge.font.bold = True
        p_badge.font.size = Pt(12)
        p_badge.font.color.rgb = WHITE
        p_badge.alignment = PP_ALIGN.CENTER

    # --- 2. IMPROVEMENT JOURNEY SECTION ---
    # Chevron tag
    chev2 = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.4), Inches(2.6), Inches(2.8), Inches(0.35))
    chev2.fill.solid()
    chev2.fill.fore_color.rgb = RGBColor(12, 60, 130)
    chev2.line.fill.background()
    p_chev2 = chev2.text_frame.paragraphs[0]
    p_chev2.text = "  2   IMPROVEMENT JOURNEY"
    p_chev2.font.bold = True
    p_chev2.font.size = Pt(11)
    p_chev2.font.color.rgb = CYAN
    p_chev2.font.name = "Arial"
    
    # Outer frame for Journey
    frame_journey = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(3.05), Inches(12.53), Inches(2.3))
    frame_journey.fill.solid()
    frame_journey.fill.fore_color.rgb = CARD_BG
    frame_journey.line.color.rgb = BORDER_BLUE
    frame_journey.line.width = Pt(1.5)

    journey_nodes = [
        ("RCA", "Root Cause\nAnalysis", "🔍", 0.7, CYAN),
        ("GAP ANALYSIS", "Identify Performance\nGaps", "🎯", 2.7, CYAN),
        ("RESKILLING /\nTRAINING", "Build Capability\n& Knowledge", "🎓", 4.7, GOLD),
        ("MONITOR &\nMEASURE", "Track KPIs\nRegularly", "📊", 6.7, CYAN),
        ("CONTINUOUS\nIMPROVEMENT", "Implement &\nImprove", "🔄", 8.7, CYAN),
        ("AUDIT & REVIEW", "Ensure Compliance\n& Sustain", "📋", 10.7, CYAN)
    ]

    for title, subtitle, icon, x, theme_color in journey_nodes:
        # Glow ring (outer circle)
        glow = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(3.2), Inches(1.0), Inches(1.0))
        glow.fill.solid()
        glow.fill.fore_color.rgb = BG_COLOR
        glow.line.color.rgb = theme_color
        glow.line.width = Pt(2)
        
        # Inner circle
        inner = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.08), Inches(3.28), Inches(0.84), Inches(0.84))
        inner.fill.solid()
        inner.fill.fore_color.rgb = theme_color
        inner.line.fill.background()
        p_inner = inner.text_frame.paragraphs[0]
        p_inner.text = icon
        p_inner.font.size = Pt(18)
        p_inner.font.color.rgb = BLACK if theme_color == GOLD else WHITE
        p_inner.alignment = PP_ALIGN.CENTER
        
        # Node Text Box
        tb = slide.shapes.add_textbox(Inches(x - 0.2), Inches(4.25), Inches(1.4), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(10)
        p1.font.color.rgb = theme_color
        p1.font.name = "Roboto"
        p1.alignment = PP_ALIGN.CENTER
        
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"
        p2.alignment = PP_ALIGN.CENTER
        
        # Connection Arrow (if not last)
        if x < 10.7:
            arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.15), Inches(3.6), Inches(0.4), Inches(0.15))
            arr.fill.solid()
            arr.fill.fore_color.rgb = CYAN
            arr.line.fill.background()

    # --- 3. RESULTS & IMPACT SECTION ---
    # Chevron tag
    chev3 = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.4), Inches(5.45), Inches(2.5), Inches(0.35))
    chev3.fill.solid()
    chev3.fill.fore_color.rgb = GREEN_BORDER
    chev3.line.fill.background()
    p_chev3 = chev3.text_frame.paragraphs[0]
    p_chev3.text = "  3   RESULTS & IMPACT"
    p_chev3.font.bold = True
    p_chev3.font.size = Pt(11)
    p_chev3.font.color.rgb = WHITE
    p_chev3.font.name = "Arial"
    
    # Outer frame for Results Grid
    results_frame = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(5.9), Inches(8.3), Inches(1.4))
    results_frame.fill.solid()
    results_frame.fill.fore_color.rgb = BG_COLOR
    results_frame.line.color.rgb = GREEN_BORDER
    results_frame.line.width = Pt(1.5)

    # BEFORE Box (Red Theme)
    before_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(6.0), Inches(2.6), Inches(1.2))
    before_box.fill.solid()
    before_box.fill.fore_color.rgb = RED_BG
    before_box.line.color.rgb = RED_BORDER
    before_box.line.width = Pt(1)
    tf_bef = before_box.text_frame
    p_bef = tf_bef.paragraphs[0]
    p_bef.text = "BEFORE:\nOTD: 92% | FTR: 91% | CSAT: 6.8"
    p_bef.font.name = "Roboto"
    p_bef.font.size = Pt(10.5)
    p_bef.font.bold = True
    p_bef.font.color.rgb = WHITE
    p_bef.alignment = PP_ALIGN.CENTER

    # Performance Improvement Center Graphic
    improve_box = slide.shapes.add_textbox(Inches(3.3), Inches(5.95), Inches(2.5), Inches(1.3))
    tf_imp = improve_box.text_frame
    p_imp = tf_imp.paragraphs[0]
    p_imp.text = "📈\nPERFORMANCE\nIMPROVEMENT"
    p_imp.font.name = "Roboto"
    p_imp.font.size = Pt(12)
    p_imp.font.bold = True
    p_imp.font.color.rgb = GOLD
    p_imp.alignment = PP_ALIGN.CENTER

    # AFTER Box (Green Theme)
    after_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.9), Inches(6.0), Inches(2.6), Inches(1.2))
    after_box.fill.solid()
    after_box.fill.fore_color.rgb = GREEN_BG
    after_box.line.color.rgb = GREEN_BORDER
    after_box.line.width = Pt(1)
    tf_aft = after_box.text_frame
    p_aft = tf_aft.paragraphs[0]
    p_aft.text = "AFTER:\nOTD: 98% | FTR: 97% | CSAT: 8.5"
    p_aft.font.name = "Roboto"
    p_aft.font.size = Pt(10.5)
    p_aft.font.bold = True
    p_aft.font.color.rgb = WHITE
    p_aft.alignment = PP_ALIGN.CENTER

    # Business Impact Right Card
    impact_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.9), Inches(5.45), Inches(4.0), Inches(1.85))
    impact_box.fill.solid()
    impact_box.fill.fore_color.rgb = CARD_BG
    impact_box.line.color.rgb = BORDER_BLUE
    impact_box.line.width = Pt(1.5)
    
    tf_impact = impact_box.text_frame
    tf_impact.word_wrap = True
    p_imp_title = tf_impact.paragraphs[0]
    p_imp_title.text = "BUSINESS IMPACT"
    p_imp_title.font.bold = True
    p_imp_title.font.size = Pt(11)
    p_imp_title.font.color.rgb = GOLD
    p_imp_title.font.name = "Roboto"
    p_imp_title.alignment = PP_ALIGN.CENTER
    
    impacts = [
        "👥 Improved Resource Capability",
        "📈 Better Demand Fulfillment",
        "🏅 Sustainable Performance Improvement"
    ]
    for imp in impacts:
        p_item = tf_impact.add_paragraph()
        p_item.text = f"• {imp}"
        p_item.font.size = Pt(9.5)
        p_item.font.color.rgb = WHITE
        p_item.font.name = "Arial"


# ==========================================
# SLIDE 2 GENERATION
# ==========================================
def build_slide_2():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_slide_title(slide, "STRATEGIC FOCUS AREAS - DRIVING PERFORMANCE & READINESS")

    # 5 Horizontal Rows
    start_y = 1.1
    row_h = 1.15
    spacing = 0.08
    
    rows_data = [
        ("TRAINING", "👨‍🏫", "Training ownership of Resource", "🎓 Focus on Skill Gaps & Continuous Learning Paths"),
        ("BUSINESS FOCAL", "🎯", "Investment to onsite coordinator at RNTBCI Premises to support demands and facilitate collaboration", "🤝 Direct Stakeholder Alignment"),
        ("KPI MANAGEMENT", "📈", "Team & Individual KPI Management through monitoring and continuous improvement", "📊 Real-time Dashboard Monitoring"),
        ("BUFFER RESOURCE", "👥", "Create trained resource pool ready-to-onboard for new demands & replacements", "🔍 Cross-trained Standby Engineers"),
        ("DELIVERY MATURITY", "⏱️", "Demonstrate delivery excellence with required KPI and readiness to transition to managed services/Workpackage", "⚙️ Quality Process SLA Assurance")
    ]

    for idx, (title, icon, desc, sub_desc) in enumerate(rows_data):
        y = start_y + idx * (row_h + spacing)
        
        # Row card
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(y), Inches(12.33), Inches(row_h))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_BLUE
        card.line.width = Pt(1)
        
        # Pointer block (left orange-gold arrow indicator)
        ptr = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.6), Inches(y + 0.15), Inches(2.6), Inches(0.85))
        ptr.fill.solid()
        ptr.fill.fore_color.rgb = GOLD
        ptr.line.fill.background()
        tf_ptr = ptr.text_frame
        p_ptr = tf_ptr.paragraphs[0]
        p_ptr.text = f" {icon}  {title}"
        p_ptr.font.bold = True
        p_ptr.font.size = Pt(12)
        p_ptr.font.color.rgb = BLACK
        p_ptr.font.name = "Roboto"
        
        # Middle text details
        tb = slide.shapes.add_textbox(Inches(3.4), Inches(y + 0.1), Inches(6.0), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = desc
        p1.font.bold = True
        p1.font.size = Pt(11)
        p1.font.color.rgb = WHITE
        p1.font.name = "Arial"
        
        p2 = tf.add_paragraph()
        p2.text = sub_desc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = CYAN
        p2.font.name = "Arial"

        # Right graphic icon box representation
        gr = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(y + 0.15), Inches(2.8), Inches(0.85))
        gr.fill.solid()
        gr.fill.fore_color.rgb = RGBColor(12, 35, 75)
        gr.line.color.rgb = CYAN
        tf_gr = gr.text_frame
        p_gr = tf_gr.paragraphs[0]
        p_gr.text = "⚡ READY & ALIGNED"
        p_gr.font.bold = True
        p_gr.font.size = Pt(10.5)
        p_gr.font.color.rgb = GOLD
        p_gr.alignment = PP_ALIGN.CENTER


# ==========================================
# SLIDE 3 GENERATION
# ==========================================
def build_slide_3():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_slide_title(slide, "RNTBCI - DEDICATED SPOC FOR SEAMLESS COORDINATION")
    
    # Subtitle
    sub_tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.75), Inches(12.33), Inches(0.4))
    p_sub = sub_tb.text_frame.paragraphs[0]
    p_sub.text = "One Point of Contact. Stronger Collaboration. Better Outcomes."
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = CYAN
    p_sub.font.name = "Arial"
    p_sub.alignment = PP_ALIGN.CENTER

    # 1. Left Column (Internal Teams)
    left_x = Inches(0.5)
    left_y_start = 1.3
    item_h = 0.8
    spacing = 0.08
    
    internal_teams = [
        ("Purchase Department", "Procurement & PO Management", "🛒"),
        ("Delivery Team", "Delivery Execution & Tracking", "🚚"),
        ("Quality Team", "Quality Assurance & Compliance", "🛡️"),
        ("PMO Team", "Planning, Tracking & Governance", "📋"),
        ("Akkodis Team", "Engineering & Onsite Delivery", "👥")
    ]
    
    for idx, (title, subtitle, icon) in enumerate(internal_teams):
        y = left_y_start + idx * (item_h + spacing)
        
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_x, Inches(y), Inches(3.2), Inches(item_h))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_BLUE
        card.line.width = Pt(1)
        
        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{icon} {title}"
        p1.font.bold = True
        p1.font.size = Pt(11)
        p1.font.color.rgb = GOLD
        p1.font.name = "Roboto"
        
        p2 = tf.add_paragraph()
        p2.text = f"  {subtitle}"
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"

    # 2. Central SPOC Target Area
    center_circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(4.5), Inches(1.3), Inches(4.3), Inches(4.3))
    center_circle.fill.solid()
    center_circle.fill.fore_color.rgb = RGBColor(10, 30, 70)
    center_circle.line.color.rgb = GOLD
    center_circle.line.width = Pt(3)
    
    tf_c = center_circle.text_frame
    tf_c.word_wrap = True
    p_c1 = tf_c.paragraphs[0]
    p_c1.text = "👤\n\nDedicated\nAkkodis SPOC\nin RNTBCI"
    p_c1.font.bold = True
    p_c1.font.size = Pt(18)
    p_c1.font.color.rgb = WHITE
    p_c1.font.name = "Times New Roman"
    p_c1.alignment = PP_ALIGN.CENTER
    
    p_c2 = tf_c.add_paragraph()
    p_c2.text = "\nPRIMARY POINT OF CONTACT\n• Documentation  • Coordination\n• Resources  • Stakeholders"
    p_c2.font.size = Pt(9.5)
    p_c2.font.color.rgb = CYAN
    p_c2.alignment = PP_ALIGN.CENTER

    # 3. Right Column (Stakeholders)
    right_x = Inches(9.6)
    
    stakeholders = [
        ("Executive Management", "Strategic Leadership & Decisions", "👤"),
        ("Delivery / Account Manager", "Oversight & Performance Review", "📊"),
        ("Technical / Project Manager", "Technical Excellence & Standards", "⚙️"),
        ("Team Leads & Engineers", "Execution & Daily Operations", "👥"),
        ("HR / TAS Team", "Talent Support & Administration", "👥")
    ]
    
    for idx, (title, subtitle, icon) in enumerate(stakeholders):
        y = left_y_start + idx * (item_h + spacing)
        
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, Inches(y), Inches(3.2), Inches(item_h))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_BLUE
        card.line.width = Pt(1)
        
        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{icon} {title}"
        p1.font.bold = True
        p1.font.size = Pt(11)
        p1.font.color.rgb = CYAN
        p1.font.name = "Roboto"
        
        p2 = tf.add_paragraph()
        p2.text = f"  {subtitle}"
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"

    # Connections representation (Central lines/arrows)
    arrow_left_to_center = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(3.8), Inches(3.2), Inches(0.6), Inches(0.2))
    arrow_left_to_center.fill.solid()
    arrow_left_to_center.fill.fore_color.rgb = GOLD
    arrow_left_to_center.line.fill.background()
    
    arrow_right_to_center = slide.shapes.add_shape(MSO_SHAPE.LEFT_ARROW, Inches(8.9), Inches(3.2), Inches(0.6), Inches(0.2))
    arrow_right_to_center.fill.solid()
    arrow_right_to_center.fill.fore_color.rgb = CYAN
    arrow_right_to_center.line.fill.background()

    # 4. Bottom Horizontal Arrow Banner
    bot_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(5.8), Inches(12.33), Inches(0.5))
    bot_banner.fill.solid()
    bot_banner.fill.fore_color.rgb = GOLD
    bot_banner.line.fill.background()
    
    tf_bb = bot_banner.text_frame
    p_bb = tf_bb.paragraphs[0]
    p_bb.text = "DRIVING SEAMLESS COORDINATION & MANAGEMENT"
    p_bb.font.bold = True
    p_bb.font.size = Pt(12)
    p_bb.font.color.rgb = BLACK
    p_bb.font.name = "Roboto"
    p_bb.alignment = PP_ALIGN.CENTER

    # 5. Bottom Icons Footer Bar
    foot_y = 6.4
    footers = [
        ("One Point of Contact", "🎯"),
        ("Stronger Collaboration", "🤝"),
        ("Greater Efficiency", "⚡"),
        ("Better Quality", "🛡️"),
        ("Superior Outcomes", "🏆")
    ]
    
    for idx, (lbl, icon) in enumerate(footers):
        x = 0.5 + idx * 2.5
        box = slide.shapes.add_textbox(Inches(x), Inches(foot_y), Inches(2.3), Inches(0.7))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{icon} {lbl}"
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = WHITE
        p.font.name = "Arial"
        p.alignment = PP_ALIGN.CENTER


# ==========================================
# SLIDE 4 GENERATION
# ==========================================
def build_slide_4():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # 1. Title
    add_slide_title(slide, "RNTBCI – PERFORMANCE SUMMARY & INSIGHTS")
    
    # Subtitle
    subBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.7), Inches(9.0), Inches(0.4))
    p_sub = subBox.text_frame.paragraphs[0]
    p_sub.text = "Driving Operational Excellence through Training, KPI Management & Seamless Support"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = GOLD
    p_sub.font.name = "Arial"
    
    # Review period box (Top-right)
    rp_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.5), Inches(0.2), Inches(2.3), Inches(0.5))
    rp_box.fill.solid()
    rp_box.fill.fore_color.rgb = CARD_BG
    rp_box.line.color.rgb = BORDER_BLUE
    tf_rp = rp_box.text_frame
    p_rp = tf_rp.paragraphs[0]
    p_rp.text = "📅 Review Period\n    Q2-CY23 – Q4-CY24"
    p_rp.font.size = Pt(9)
    p_rp.font.color.rgb = WHITE
    p_rp.font.name = "Arial"

    # --- TOP ROW ---
    # 2. Left Columns: Metric Cards
    # OTD Card
    otd_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.2), Inches(3.0), Inches(1.3))
    otd_card.fill.solid()
    otd_card.fill.fore_color.rgb = CARD_BG
    otd_card.line.color.rgb = BORDER_BLUE
    tf_otd = otd_card.text_frame
    p_o1 = tf_otd.paragraphs[0]
    p_o1.text = "🚚 OTD (On Time Delivery)"
    p_o1.font.bold = True
    p_o1.font.size = Pt(11)
    p_o1.font.color.rgb = WHITE
    
    p_o2 = tf_otd.add_paragraph()
    p_o2.text = "97.6%"
    p_o2.font.bold = True
    p_o2.font.size = Pt(20)
    p_o2.font.color.rgb = GREEN_BORDER
    
    p_o3 = tf_otd.add_paragraph()
    p_o3.text = "📈 +9.2% Improvement from Q2-CY23"
    p_o3.font.size = Pt(9)
    p_o3.font.color.rgb = GREEN_BORDER

    # FTR Card
    ftr_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(2.6), Inches(3.0), Inches(1.3))
    ftr_card.fill.solid()
    ftr_card.fill.fore_color.rgb = CARD_BG
    ftr_card.line.color.rgb = BORDER_BLUE
    tf_ftr = ftr_card.text_frame
    p_f1 = tf_ftr.paragraphs[0]
    p_f1.text = "📋 FTR (First Time Resolution)"
    p_f1.font.bold = True
    p_f1.font.size = Pt(11)
    p_f1.font.color.rgb = WHITE
    
    p_f2 = tf_ftr.add_paragraph()
    p_f2.text = "96.8%"
    p_f2.font.bold = True
    p_f2.font.size = Pt(20)
    p_f2.font.color.rgb = GREEN_BORDER
    
    p_f3 = tf_ftr.add_paragraph()
    p_f3.text = "📈 +8.7% Improvement from Q2-CY23"
    p_f3.font.size = Pt(9)
    p_f3.font.color.rgb = GREEN_BORDER

    # 3. Middle Column: OTD & FTR quarterly trend chart
    chart_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.7), Inches(1.2), Inches(5.3), Inches(2.6))
    chart_bg.fill.solid()
    chart_bg.fill.fore_color.rgb = CARD_BG
    chart_bg.line.color.rgb = BORDER_BLUE
    
    tf_ch = chart_bg.text_frame
    p_ch = tf_ch.paragraphs[0]
    p_ch.text = "OTD & FTR QUARTERLY TREND"
    p_ch.font.bold = True
    p_ch.font.size = Pt(11)
    p_ch.font.color.rgb = GOLD
    p_ch.alignment = PP_ALIGN.CENTER

    # Render simulated bars for the chart
    quarters = ["Q2-CY23", "Q3-CY23", "Q4-CY23", "Q1-CY24", "Q2-CY24", "Q3-CY24", "Q4-CY24"]
    otd_vals = [88.4, 91.2, 94.6, 97.8, 97.1, 96.3, 97.9]
    ftr_vals = [88.1, 90.3, 93.4, 96.6, 96.2, 95.1, 98.0]
    
    # We will draw a mini bar representation
    for i in range(7):
        x_q = 3.9 + (i * 0.7)
        # OTD bar (green)
        h_otd = (otd_vals[i] - 70) * 0.04  # scale factor
        bar_o = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x_q), Inches(3.3 - h_otd), Inches(0.2), Inches(h_otd))
        bar_o.fill.solid()
        bar_o.fill.fore_color.rgb = GREEN_BORDER
        bar_o.line.fill.background()
        
        # FTR bar (blue)
        h_ftr = (ftr_vals[i] - 70) * 0.04
        bar_f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x_q + 0.22), Inches(3.3 - h_ftr), Inches(0.2), Inches(h_ftr))
        bar_f.fill.solid()
        bar_f.fill.fore_color.rgb = CYAN
        bar_f.line.fill.background()
        
        # Quarter text label below
        tb_q = slide.shapes.add_textbox(Inches(x_q - 0.1), Inches(3.3), Inches(0.6), Inches(0.35))
        tb_q.text_frame.word_wrap = False
        tb_q.text_frame.margin_left = tb_q.text_frame.margin_right = tb_q.text_frame.margin_top = tb_q.text_frame.margin_bottom = 0
        p_q = tb_q.text_frame.paragraphs[0]
        p_q.text = quarters[i]
        p_q.font.size = Pt(7.5)
        p_q.font.color.rgb = WHITE
        p_q.alignment = PP_ALIGN.CENTER

    # 4. Right Column Top: FTE Count Chart
    fte_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.2), Inches(1.2), Inches(3.6), Inches(1.3))
    fte_bg.fill.solid()
    fte_bg.fill.fore_color.rgb = CARD_BG
    fte_bg.line.color.rgb = BORDER_BLUE
    
    tf_fte = fte_bg.text_frame
    p_fte = tf_fte.paragraphs[0]
    p_fte.text = "FTE COUNT (Quarterly)"
    p_fte.font.bold = True
    p_fte.font.size = Pt(10.5)
    p_fte.font.color.rgb = GOLD
    p_fte.alignment = PP_ALIGN.CENTER
    
    # Render mini bars for FTE
    fte_vals = [6, 9, 14, 19, 17, 4, 2]
    for i in range(7):
        x_f = 9.35 + (i * 0.46)
        h_fte = fte_vals[i] * 0.04
        bar_ft = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x_f), Inches(2.2 - h_fte), Inches(0.2), Inches(h_fte))
        bar_ft.fill.solid()
        bar_ft.fill.fore_color.rgb = GOLD
        bar_ft.line.fill.background()
        
        # Label below bar
        tb_fl = slide.shapes.add_textbox(Inches(x_f - 0.1), Inches(2.2), Inches(0.4), Inches(0.25))
        tb_fl.text_frame.word_wrap = False
        tb_fl.text_frame.margin_left = tb_fl.text_frame.margin_right = tb_fl.text_frame.margin_top = tb_fl.text_frame.margin_bottom = 0
        p_fl = tb_fl.text_frame.paragraphs[0]
        p_fl.text = str(fte_vals[i])
        p_fl.font.size = Pt(7.5)
        p_fl.font.bold = True
        p_fl.font.color.rgb = WHITE
        p_fl.alignment = PP_ALIGN.CENTER

    # 5. Right Column Bottom: Domain and Target Details
    dt_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.2), Inches(2.6), Inches(3.6), Inches(1.2))
    dt_bg.fill.solid()
    dt_bg.fill.fore_color.rgb = CARD_BG
    dt_bg.line.color.rgb = BORDER_BLUE
    
    tf_dt = dt_bg.text_frame
    tf_dt.word_wrap = True
    p_dt = tf_dt.paragraphs[0]
    p_dt.text = "🏛️ DOMAIN SUPPORTED:\n  Exteriors | Lighting\n\n🎯 KPI TARGET: OTD > 95% | FTR > 95%"
    p_dt.font.size = Pt(9.5)
    p_dt.font.color.rgb = WHITE
    p_dt.font.name = "Arial"
    p_dt.alignment = PP_ALIGN.CENTER

    # --- MIDDLE ROW (THREE COLUMNS) ---
    col_w = Inches(3.9)
    col_h = Inches(2.2)
    col_y = Inches(4.0)

    # Column 1: KEY LEARNINGS (Green badge)
    c1_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), col_y, col_w, col_h)
    c1_bg.fill.solid()
    c1_bg.fill.fore_color.rgb = GREEN_BG
    c1_bg.line.color.rgb = GREEN_BORDER
    c1_bg.line.width = Pt(1.5)
    
    tf_c1 = c1_bg.text_frame
    tf_c1.word_wrap = True
    p_c1_t = tf_c1.paragraphs[0]
    p_c1_t.text = "💡 KEY LEARNINGS"
    p_c1_t.font.bold = True
    p_c1_t.font.size = Pt(12)
    p_c1_t.font.color.rgb = WHITE
    
    learnings = [
        "✅ NPDM & MEET Inhouse training setup",
        "✅ Active Skill Matrix Monitoring",
        "✅ KPI Management & Governance",
        "✅ Optimization of Resource Pools",
        "✅ Alignment on JD10 Methodologies",
        "✅ Dedicated Coordinator Assignment"
    ]
    for l in learnings:
        p_l = tf_c1.add_paragraph()
        p_l.text = l
        p_l.font.size = Pt(9.5)
        p_l.font.color.rgb = WHITE

    # Column 2: KEY CHALLENGES (Red badge)
    c2_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.7), col_y, col_w, col_h)
    c2_bg.fill.solid()
    c2_bg.fill.fore_color.rgb = RED_BG
    c2_bg.line.color.rgb = RED_BORDER
    c2_bg.line.width = Pt(1.5)
    
    tf_c2 = c2_bg.text_frame
    tf_c2.word_wrap = True
    p_c2_t = tf_c2.paragraphs[0]
    p_c2_t.text = "⚠️ KEY CHALLENGES"
    p_c2_t.font.bold = True
    p_c2_t.font.size = Pt(12)
    p_c2_t.font.color.rgb = WHITE
    
    challenges = [
        "❌ Deployment delay to RNTBCI",
        "❌ Training slot availability at RNTBCI",
        "❌ Purchase Order (PO) release delay",
        "❌ Timesheet submission tracking lag"
    ]
    for c in challenges:
        p_c = tf_c2.add_paragraph()
        p_c.text = c
        p_c.font.size = Pt(9.5)
        p_c.font.color.rgb = WHITE

    # Column 3: KEY TAKEAWAYS (Blue badge)
    c3_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.9), col_y, col_w, col_h)
    c3_bg.fill.solid()
    c3_bg.fill.fore_color.rgb = CARD_BG
    c3_bg.line.color.rgb = BORDER_BLUE
    c3_bg.line.width = Pt(1.5)
    
    tf_c3 = c3_bg.text_frame
    tf_c3.word_wrap = True
    p_c3_t = tf_c3.paragraphs[0]
    p_c3_t.text = "🎯 KEY TAKEAWAYS"
    p_c3_t.font.bold = True
    p_c3_t.font.size = Pt(12)
    p_c3_t.font.color.rgb = CYAN
    
    takeaways = [
        "🔵 Sustained performance >95% target since Q4-CY23",
        "🔵 Effective training & KPI management results",
        "🔵 Optimized resource utilization with reduced FTE",
        "🔵 Ready foundation to transition to Managed Services"
    ]
    for t in takeaways:
        p_t = tf_c3.add_paragraph()
        p_t.text = t
        p_t.font.size = Pt(9.5)
        p_t.font.color.rgb = WHITE


    # --- BOTTOM ROW (FOCUS NEXT BANNER) ---
    focus_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(6.35), Inches(12.33), Inches(0.6))
    focus_bg.fill.solid()
    focus_bg.fill.fore_color.rgb = CARD_BG
    focus_bg.line.color.rgb = GOLD
    
    tf_f = focus_bg.text_frame
    tf_f.word_wrap = True
    p_f = tf_f.paragraphs[0]
    p_f.text = "📋 FOCUS NEXT:  🎓 Continue training & skills  |  👥 Resource forecasting  |  🔄 Streamline POs  |  🕒 Improve Timesheet accuracy"
    p_f.font.bold = True
    p_f.font.size = Pt(10.5)
    p_f.font.color.rgb = GOLD
    p_f.alignment = PP_ALIGN.CENTER


# ==========================================
# SLIDE 5 GENERATION
# ==========================================
def build_slide_5():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # 1. Custom Title
    # We want a split title "ENGINEERING EXCELLENCE | INNOVATE. VALIDATE. DELIVER."
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.33), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    run1 = p.add_run()
    run1.text = "ENGINEERING EXCELLENCE  |  "
    run1.font.name = "Times New Roman"
    run1.font.size = Pt(26)
    run1.font.bold = True
    run1.font.color.rgb = WHITE
    
    run2 = p.add_run()
    run2.text = "INNOVATE. VALIDATE. DELIVER."
    run2.font.name = "Times New Roman"
    run2.font.size = Pt(26)
    run2.font.bold = True
    run2.font.color.rgb = GOLD
    p.alignment = PP_ALIGN.CENTER

    # --- LEFT COLUMN: KEY ACTIVITIES ---
    act_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.1), Inches(2.6), Inches(5.1))
    act_bg.fill.solid()
    act_bg.fill.fore_color.rgb = CARD_BG
    act_bg.line.color.rgb = BORDER_BLUE
    act_bg.line.width = Pt(1.5)
    
    tf_act = act_bg.text_frame
    tf_act.word_wrap = True
    p_act = tf_act.paragraphs[0]
    p_act.text = "📋 KEY ACTIVITIES"
    p_act.font.bold = True
    p_act.font.size = Pt(12)
    p_act.font.color.rgb = GOLD
    
    activities = [
        "📊 Soft Benchmarking",
        "🛡️ Surface Feasibility Study",
        "📄 Packaging & Regs Study",
        "📐 Master Sections",
        "📦 3D CAD modeling",
        "👥 CFT discussions",
        "🎯 PMI GD&T Stackup",
        "📄 Engg Drawing & BOM",
        "👤 Design Release",
        "📈 VAVE",
        "🤝 Supplier Management"
    ]
    for act in activities:
        p_item = tf_act.add_paragraph()
        p_item.text = act
        p_item.font.size = Pt(9)
        p_item.font.color.rgb = WHITE
        p_item.font.name = "Arial"

    # --- CENTER GRID: 6 DOMAINS (WITH GENERATED IMAGES) ---
    grid_data = [
        ("🚗 BIW", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\biw_chassis_frame_1784568686423.png", 3.15, 1.1),
        ("🚗 EXTERIOR", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\car_exterior_side_1784568705359.png", 5.4, 1.1),
        ("🛋️ INTERIOR", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\car_interior_cockpit_1784568728606.png", 7.65, 1.1),
        ("💺 SEATING", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\car_sport_seats_1784568751946.png", 3.15, 3.0),
        ("💡 LIGHTING", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\car_lighting_taillights_1784568772871.png", 5.4, 3.0),
        ("🚗 CHASSIS", r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\7c9e712e-098a-4195-a7c3-faa0bd382552\car_chassis_suspension_1784568794971.png", 7.65, 3.0)
    ]

    for title, img_path, x, y in grid_data:
        # Dotted border card background
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(2.15), Inches(1.8))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = GOLD
        card.line.width = Pt(1.2)
        
        # Title of card
        tb_c = slide.shapes.add_textbox(Inches(x + 0.1), Inches(y + 0.05), Inches(1.95), Inches(0.35))
        tf_c = tb_c.text_frame
        p_c = tf_c.paragraphs[0]
        p_c.text = title
        p_c.font.bold = True
        p_c.font.size = Pt(10.5)
        p_c.font.color.rgb = WHITE
        p_c.font.name = "Roboto"
        
        # Add generated image
        try:
            slide.shapes.add_picture(img_path, Inches(x + 0.1), Inches(y + 0.4), Inches(1.95), Inches(1.3))
        except Exception as e:
            # Fallback if image not found
            fallback = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.1), Inches(y + 0.4), Inches(1.95), Inches(1.3))
            fallback.fill.solid()
            fallback.fill.fore_color.rgb = RGBColor(20, 35, 60)
            fallback.text = "[Image Preview]"
            fallback.text_frame.paragraphs[0].font.size = Pt(8)

    # --- CENTER BOTTOM: QUALITY PROCESSES ---
    qp_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.15), Inches(4.9), Inches(6.65), Inches(1.3))
    qp_bg.fill.solid()
    qp_bg.fill.fore_color.rgb = CARD_BG
    qp_bg.line.color.rgb = BORDER_BLUE
    qp_bg.line.width = Pt(1.5)
    
    tf_qp = qp_bg.text_frame
    tf_qp.word_wrap = True
    p_qp = tf_qp.paragraphs[0]
    p_qp.text = "QUALITY PROCESSES"
    p_qp.font.bold = True
    p_qp.font.size = Pt(11)
    p_qp.font.color.rgb = GOLD
    p_qp.alignment = PP_ALIGN.CENTER
    
    q_items = [
        ("📋 DFMEA", "Design Failure Mode\n& Effects Analysis", 3.3),
        ("🛡️ PPAP", "Production Part\nApproval Process", 5.45),
        ("⚙️ APQP", "Advanced Product\nQuality Planning", 7.6)
    ]
    for q_title, q_desc, q_x in q_items:
        tb_q = slide.shapes.add_textbox(Inches(q_x), Inches(5.2), Inches(2.0), Inches(0.95))
        tf_q = tb_q.text_frame
        tf_q.word_wrap = True
        
        p1 = tf_q.paragraphs[0]
        p1.text = q_title
        p1.font.bold = True
        p1.font.size = Pt(10)
        p1.font.color.rgb = CYAN
        p1.font.name = "Roboto"
        
        p2 = tf_q.add_paragraph()
        p2.text = q_desc
        p2.font.size = Pt(8)
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"

    # --- RIGHT COLUMN: TOOLS ---
    tools_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.3), Inches(1.1), Inches(2.6), Inches(5.1))
    tools_bg.fill.solid()
    tools_bg.fill.fore_color.rgb = CARD_BG
    tools_bg.line.color.rgb = BORDER_BLUE
    tools_bg.line.width = Pt(1.5)
    
    tf_tools = tools_bg.text_frame
    tf_tools.word_wrap = True
    p_tl = tf_tools.paragraphs[0]
    p_tl.text = "🛠️ TOOLS"
    p_tl.font.bold = True
    p_tl.font.size = Pt(12)
    p_tl.font.color.rgb = GOLD
    
    tools = [
        " Siemens NX",
        " CATIA",
        " ENOVIA",
        " 3DEXPERIENCE",
        " Jira",
        " Teamcenter"
    ]
    for t in tools:
        p_t = tf_tools.add_paragraph()
        p_t.text = f"⚙️ {t}"
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = CYAN
        p_t.font.name = "Arial"

    # --- BOTTOM ROW (FOCUS BANNER) ---
    bot_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(6.35), Inches(12.5), Inches(0.6))
    bot_banner.fill.solid()
    bot_banner.fill.fore_color.rgb = CARD_BG
    bot_banner.line.color.rgb = GOLD
    
    tf_bb = bot_banner.text_frame
    tf_bb.word_wrap = True
    p_bb = tf_bb.paragraphs[0]
    p_bb.text = "🎯 HIGHER QUALITY  |  ⚡ FASTER TIME TO MARKET  |  💲 COST OPTIMIZATION  |  👥 STRONG COLLABORATION  |  🛡️ COMPLIANCE"
    p_bb.font.bold = True
    p_bb.font.size = Pt(10.5)
    p_bb.font.color.rgb = GOLD
    p_bb.alignment = PP_ALIGN.CENTER


# ==========================================
# SLIDE 6 GENERATION
# ==========================================
def build_slide_6():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # 1. Slide Title
    add_slide_title(slide, "EXPECTED COMPETENCY & CAPACITY / SERVICE TIME ACCEPTANCE")
    
    # 2. Akkodis White Logo (top right)
    logo_path = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons\logo_akkodis_white.png"
    try:
        slide.shapes.add_picture(logo_path, Inches(10.8), Inches(0.2), Inches(2.0), Inches(0.4))
    except Exception as e:
        print(f"Error adding logo: {e}")

    # Theme colors reference
    # CARD_BG = RGBColor(8, 22, 50)
    # BORDER_BLUE = RGBColor(12, 50, 100)
    # GOLD = RGBColor(255, 184, 28)
    # CYAN = RGBColor(0, 255, 255)
    # WHITE = RGBColor(255, 255, 255)
    # TEXT_MUTED = RGBColor(160, 180, 200)

    # 3. Left Sidebar Column Categories
    sidebar_y_coords = [1.1, 2.65, 4.2]
    sidebar_data = [
        ("PEOPLE & EXPERTISE", "icon_people.png", "Multi-domain competencies with deep industry experience"),
        ("SCALE & CAPACITY", "icon_scale.png", "Right size capacity with flexibility to scale up / down"),
        ("SERVICE EXCELLENCE", "icon_excellence.png", "Operational excellence with SLA & KPI focus")
    ]
    
    icons_dir = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons"
    
    for idx, (title, icon_file, desc) in enumerate(sidebar_data):
        y = sidebar_y_coords[idx]
        
        # Category Card
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(y), Inches(2.5), Inches(1.4))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_BLUE
        card.line.width = Pt(1.5)
        
        # Category Icon
        try:
            icon_path = os.path.join(icons_dir, icon_file)
            slide.shapes.add_picture(icon_path, Inches(0.55), Inches(y + 0.15), Inches(0.4), Inches(0.4))
        except Exception as e:
            print(f"Error adding sidebar icon {icon_file}: {e}")
            
        # Category Text Box
        tb = slide.shapes.add_textbox(Inches(1.0), Inches(y + 0.05), Inches(1.8), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.05)
        
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = GOLD
        p1.font.name = "Roboto"
        
        p2 = tf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"

    # Category Block 4: Service Time Acceptance Left Category Box
    card4 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(5.75), Inches(2.5), Inches(0.9))
    card4.fill.solid()
    card4.fill.fore_color.rgb = CARD_BG
    card4.line.color.rgb = BORDER_BLUE
    card4.line.width = Pt(1.5)
    
    try:
        icon_path = os.path.join(icons_dir, "icon_business_hours.png")
        slide.shapes.add_picture(icon_path, Inches(0.55), Inches(5.9), Inches(0.4), Inches(0.4))
    except Exception as e:
        print(f"Error adding sidebar icon: {e}")
        
    tb4 = slide.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(1.8), Inches(0.8))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_right = tf4.margin_top = tf4.margin_bottom = Inches(0.05)
    p_b4 = tf4.paragraphs[0]
    p_b4.text = "SERVICE TIME\nACCEPTANCE"
    p_b4.font.bold = True
    p_b4.font.size = Pt(10.5)
    p_b4.font.color.rgb = GOLD
    p_b4.font.name = "Roboto"

    # 4. Grid of 9 Competency Cards
    cards_data = [
        # (title, icon_file, stars, competency, capacity, capacity_color, col, row)
        ("SAFe / Agile Delivery", "icon_safe.png", 5, "EXPERT", "HIGH", GREEN_BORDER, 0, 0),
        ("Application Support & ITSM", "icon_support.png", 5, "EXPERT", "HIGH", GREEN_BORDER, 1, 0),
        ("DevSecOps & CI/CD", "icon_devsecops.png", 4, "ADVANCED", "HIGH", GREEN_BORDER, 2, 0),
        
        ("Cloud & OpenShift", "icon_cloud.png", 4, "ADVANCED", "HIGH", GREEN_BORDER, 0, 1),
        ("PLM & Engg. Applications", "icon_plm.png", 4, "ADVANCED", "MEDIUM", GOLD, 1, 1),
        ("SCADA & Ind. Dashboards", "icon_scada.png", 4, "ADVANCED", "MEDIUM", GOLD, 2, 1),
        
        ("AR/VR & Mixed Reality", "icon_arvr.png", 4, "ADVANCED", "MEDIUM", GOLD, 0, 2),
        ("Quality Engg. & Testing", "icon_quality.png", 5, "EXPERT", "HIGH", GREEN_BORDER, 1, 2),
        ("Architecture & Consulting", "icon_architecture.png", 5, "EXPERT", "MEDIUM", GOLD, 2, 2)
    ]
    
    for title, icon_file, stars, competency, capacity, cap_color, col, row in cards_data:
        cx = 3.0 + col * 2.55
        cy = 1.1 + row * 1.55
        cw = 2.45
        ch = 1.4
        
        # Grid Card Shape
        g_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(cx), Inches(cy), Inches(cw), Inches(ch))
        g_card.fill.solid()
        g_card.fill.fore_color.rgb = CARD_BG
        g_card.line.color.rgb = BORDER_BLUE
        g_card.line.width = Pt(1)
        
        # Card Icon
        try:
            icon_path = os.path.join(icons_dir, icon_file)
            slide.shapes.add_picture(icon_path, Inches(cx + 0.12), Inches(cy + 0.15), Inches(0.45), Inches(0.45))
        except Exception as e:
            print(f"Error adding card icon {icon_file}: {e}")
            
        # Card Title Box
        tb_t = slide.shapes.add_textbox(Inches(cx + 0.65), Inches(cy + 0.1), Inches(1.7), Inches(0.45))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = Inches(0.02)
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = WHITE
        p_t.font.name = "Roboto"
        
        # Card Ratings and Competency / Capacity Details
        tb_d = slide.shapes.add_textbox(Inches(cx + 0.12), Inches(cy + 0.65), Inches(2.2), Inches(0.7))
        tf_d = tb_d.text_frame
        tf_d.word_wrap = True
        tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = Inches(0.02)
        
        # Stars rating paragraph
        p_stars = tf_d.paragraphs[0]
        run_filled = p_stars.add_run()
        run_filled.text = "★" * stars
        run_filled.font.color.rgb = GOLD
        run_filled.font.size = Pt(12)
        if stars < 5:
            run_empty = p_stars.add_run()
            run_empty.text = "☆" * (5 - stars)
            run_empty.font.color.rgb = TEXT_MUTED
            run_empty.font.size = Pt(12)
            
        # Competency paragraph
        p_comp = tf_d.add_paragraph()
        run_c1 = p_comp.add_run()
        run_c1.text = "Competency: "
        run_c1.font.size = Pt(9.5)
        run_c1.font.color.rgb = TEXT_MUTED
        run_c2 = p_comp.add_run()
        run_c2.text = competency
        run_c2.font.bold = True
        run_c2.font.size = Pt(9.5)
        run_c2.font.color.rgb = CYAN
        
        # Capacity paragraph
        p_cap = tf_d.add_paragraph()
        run_cp1 = p_cap.add_run()
        run_cp1.text = "Capacity: "
        run_cp1.font.size = Pt(9.5)
        run_cp1.font.color.rgb = TEXT_MUTED
        run_cp2 = p_cap.add_run()
        run_cp2.text = capacity
        run_cp2.font.bold = True
        run_cp2.font.size = Pt(9.5)
        run_cp2.font.color.rgb = WHITE
        
        # Capacity status circle badge
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + cw - 0.35), Inches(cy + ch - 0.35), Inches(0.18), Inches(0.18))
        dot.fill.solid()
        dot.fill.fore_color.rgb = cap_color
        dot.line.fill.background()

    # 5. Right Sidebar (Competency Scale & Capacity Indicator Legends)
    # Block 5A: Competency Scale Legend Card
    leg_scale = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.65), Inches(1.1), Inches(2.3), Inches(2.2))
    leg_scale.fill.solid()
    leg_scale.fill.fore_color.rgb = CARD_BG
    leg_scale.line.color.rgb = BORDER_BLUE
    leg_scale.line.width = Pt(1.5)
    
    tb_ls = slide.shapes.add_textbox(Inches(10.75), Inches(1.15), Inches(2.1), Inches(2.1))
    tf_ls = tb_ls.text_frame
    tf_ls.word_wrap = True
    tf_ls.margin_left = tf_ls.margin_right = tf_ls.margin_top = tf_ls.margin_bottom = Inches(0.02)
    
    p_lst = tf_ls.paragraphs[0]
    p_lst.text = "COMPETENCY SCALE"
    p_lst.font.bold = True
    p_lst.font.size = Pt(10.5)
    p_lst.font.color.rgb = GOLD
    p_lst.font.name = "Roboto"
    
    scales_legend = [
        (5, "5 - Expert / CoE"),
        (4, "4 - Advanced"),
        (3, "3 - Competent"),
        (2, "2 - Developing"),
        (1, "1 - Basic")
    ]
    for s_val, s_text in scales_legend:
        p_sc = tf_ls.add_paragraph()
        run_f = p_sc.add_run()
        run_f.text = "★" * s_val
        run_f.font.color.rgb = GOLD
        run_f.font.size = Pt(10.5)
        if s_val < 5:
            run_e = p_sc.add_run()
            run_e.text = "☆" * (5 - s_val)
            run_e.font.color.rgb = TEXT_MUTED
            run_e.font.size = Pt(10.5)
        run_t = p_sc.add_run()
        run_t.text = f" {s_text}"
        run_t.font.size = Pt(8.5)
        run_t.font.color.rgb = WHITE
        run_t.font.name = "Arial"

    # Block 5B: Capacity Indicator Legend Card
    leg_cap = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.65), Inches(3.4), Inches(2.3), Inches(2.2))
    leg_cap.fill.solid()
    leg_cap.fill.fore_color.rgb = CARD_BG
    leg_cap.line.color.rgb = BORDER_BLUE
    leg_cap.line.width = Pt(1.5)
    
    tb_lc = slide.shapes.add_textbox(Inches(10.75), Inches(3.45), Inches(2.1), Inches(2.1))
    tf_lc = tb_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_right = tf_lc.margin_top = tf_lc.margin_bottom = Inches(0.02)
    
    p_lct = tf_lc.paragraphs[0]
    p_lct.text = "CAPACITY INDICATOR"
    p_lct.font.bold = True
    p_lct.font.size = Pt(10.5)
    p_lct.font.color.rgb = GOLD
    p_lct.font.name = "Roboto"
    
    capacity_legend = [
        (GREEN_BORDER, "HIGH\nSufficient capacity\navailable"),
        (GOLD, "MEDIUM\nAvailable with\nplanned ramp-up"),
        (RED_BORDER, "LOW\nNiche capability /\nPartner support")
    ]
    
    for idx, (cap_col, cap_desc) in enumerate(capacity_legend):
        # Y position for indicators
        y_dot = 3.95 + idx * 0.55
        
        # Add Dot Shape
        i_dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.8), Inches(y_dot), Inches(0.12), Inches(0.12))
        i_dot.fill.solid()
        i_dot.fill.fore_color.rgb = cap_col
        i_dot.line.fill.background()
        
        # Add Description Textbox next to Dot
        tb_desc = slide.shapes.add_textbox(Inches(10.98), Inches(y_dot - 0.08), Inches(1.9), Inches(0.55))
        tf_desc = tb_desc.text_frame
        tf_desc.word_wrap = True
        tf_desc.margin_left = tf_desc.margin_right = tf_desc.margin_top = tf_desc.margin_bottom = 0
        
        lines = cap_desc.split("\n")
        p_desc = tf_desc.paragraphs[0]
        run_tit = p_desc.add_run()
        run_tit.text = lines[0]
        run_tit.font.bold = True
        run_tit.font.size = Pt(8.5)
        run_tit.font.color.rgb = cap_col
        
        p_sub = tf_desc.add_paragraph()
        run_sub = p_sub.add_run()
        run_sub.text = lines[1]
        run_sub.font.size = Pt(8)
        run_sub.font.color.rgb = WHITE

    # 6. Bottom Row: Service Time Acceptance
    sta_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.0), Inches(5.75), Inches(9.95), Inches(0.9))
    sta_bg.fill.solid()
    sta_bg.fill.fore_color.rgb = CARD_BG
    sta_bg.line.color.rgb = BORDER_BLUE
    sta_bg.line.width = Pt(1.5)
    
    service_items = [
        ("Business Hours\nSupport", "icon_business_hours.png", "09:00 - 18:00 IST"),
        ("Extended Coverage\n(as required)", "icon_extended_coverage.png", "12:30 - 21:30 IST"),
        ("24x7 Incident\nSupport", "icon_24_7.png", "24x7 Support"),
        ("Major Incident\nReadiness", "icon_siren.png", "Major Incident"),
        ("Weekend / Release\nSupport", "icon_calendar.png", "As per plan"),
        ("SLA / KPI\nCompliance", "icon_sla.png", "SLA Compliant"),
        ("Hypercare & Early\nLife Support", "icon_hypercare.png", "Hypercare Support")
    ]
    
    for idx, (sta_title, sta_icon, sta_desc) in enumerate(service_items):
        item_x = 3.05 + idx * 1.41
        
        # Add Icon
        try:
            icon_path = os.path.join(icons_dir, sta_icon)
            slide.shapes.add_picture(icon_path, Inches(item_x), Inches(5.95), Inches(0.35), Inches(0.35))
        except Exception as e:
            print(f"Error adding sta icon {sta_icon}: {e}")
            
        # Add Textbox
        tb_s = slide.shapes.add_textbox(Inches(item_x + 0.38), Inches(5.8), Inches(0.98), Inches(0.8))
        tf_s = tb_s.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_right = tf_s.margin_top = tf_s.margin_bottom = 0
        
        p_st1 = tf_s.paragraphs[0]
        p_st1.text = sta_title.split("\n")[0]
        if len(sta_title.split("\n")) > 1:
            p_st1.text += " " + sta_title.split("\n")[1]
        p_st1.font.bold = True
        p_st1.font.size = Pt(8)
        p_st1.font.color.rgb = WHITE
        p_st1.font.name = "Roboto"
        
        p_st2 = tf_s.add_paragraph()
        p_st2.text = f"\n{sta_desc}"
        p_st2.font.size = Pt(7.5)
        p_st2.font.color.rgb = CYAN
        p_st2.font.name = "Arial"

    # 7. Bottom Commitment Banner
    bot_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(6.8), Inches(12.53), Inches(0.55))
    bot_banner.fill.solid()
    bot_banner.fill.fore_color.rgb = CARD_BG
    bot_banner.line.color.rgb = GOLD
    bot_banner.line.width = Pt(1.5)
    
    # Target Icon
    try:
        icon_path = os.path.join(icons_dir, "icon_target.png")
        slide.shapes.add_picture(icon_path, Inches(0.6), Inches(6.85), Inches(0.45), Inches(0.45))
    except Exception as e:
        print(f"Error adding target icon: {e}")
        
    # Textbox next to icon
    tb_b = slide.shapes.add_textbox(Inches(1.15), Inches(6.82), Inches(11.5), Inches(0.5))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0
    p_b = tf_b.paragraphs[0]
    
    run_main1 = p_b.add_run()
    run_main1.text = "Our commitment: Right skills, right capacity, right time – delivering consistent "
    run_main1.font.size = Pt(10.5)
    run_main1.font.color.rgb = WHITE
    run_main1.font.name = "Arial"
    
    run_main2 = p_b.add_run()
    run_main2.text = "service excellence"
    run_main2.font.bold = True
    run_main2.font.size = Pt(10.5)
    run_main2.font.color.rgb = CYAN
    run_main2.font.name = "Arial"
    
    run_main3 = p_b.add_run()
    run_main3.text = ", "
    run_main3.font.size = Pt(10.5)
    run_main3.font.color.rgb = WHITE
    run_main3.font.name = "Arial"
    
    run_main4 = p_b.add_run()
    run_main4.text = "SLA performance"
    run_main4.font.bold = True
    run_main4.font.size = Pt(10.5)
    run_main4.font.color.rgb = GOLD
    run_main4.font.name = "Arial"
    
    run_main5 = p_b.add_run()
    run_main5.text = " and "
    run_main5.font.size = Pt(10.5)
    run_main5.font.color.rgb = WHITE
    run_main5.font.name = "Arial"
    
    run_main6 = p_b.add_run()
    run_main6.text = "business value"
    run_main6.font.bold = True
    run_main6.font.size = Pt(10.5)
    run_main6.font.color.rgb = CYAN
    run_main6.font.name = "Arial"
    
    run_main7 = p_b.add_run()
    run_main7.text = " for Airbus Digital for Operations."
    run_main7.font.size = Pt(10.5)
    run_main7.font.color.rgb = WHITE
    run_main7.font.name = "Arial"


# ==========================================
# SLIDE 7 GENERATION
# ==========================================
def build_slide_7():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons"

    # 1. Slide Title & Logo
    add_slide_title(slide, "Governed. Standardized. Automated. Optimized.")
    logo_path = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons\logo_akkodis_white.png"
    try:
        slide.shapes.add_picture(logo_path, Inches(10.8), Inches(0.2), Inches(2.0), Inches(0.4))
    except Exception as e:
        print(f"Error adding logo: {e}")

    # --- TOP COLUMN HEADERS ---
    # Column 1: Governance Pyramid Header
    draw_card(0.4, 0.7, 4.2, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 0.75, 4.0, 0.25, [{"text": "GOVERNANCE PYRAMID", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Column 2: Governance Structure Header
    draw_card(4.8, 0.7, 3.1, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(4.9, 0.75, 2.9, 0.25, [{"text": "GOVERNANCE STRUCTURE", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Column 3: CoE Header
    draw_card(8.0, 0.7, 2.6, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.1, 0.75, 2.4, 0.25, [{"text": "CENTER OF EXCELLENCE (CoE)", "bold": True, "size": 10.5, "color": GOLD}], PP_ALIGN.CENTER)

    # Column 4: Meeting Cadence Header
    draw_card(10.7, 0.7, 2.2, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(10.8, 0.75, 2.0, 0.25, [{"text": "MEETING CADENCE", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    # --- COLUMN 1: GOVERNANCE PYRAMID ---
    # Levels Column on left of Pyramid
    pyramid_levels = [
        ("EXECUTIVE", "Annual / Bi-Annual", "icon_people.png", 1.15),
        ("STRATEGIC", "Quarterly", "icon_target.png", 1.95),
        ("TACTICAL", "Monthly", "icon_excellence.png", 2.75),
        ("OPERATIONAL", "Weekly / Daily", "icon_people.png", 3.55)
    ]
    
    # Draw vertical dashed-like connection lines for frequency flow
    draw_connector_line(0.85, 1.45, 0.02, 2.2, BORDER_BLUE)

    for title, freq, icon_file, y in pyramid_levels:
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.65), Inches(y), Inches(0.4), Inches(0.4))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(1)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(0.7), Inches(y + 0.05), Inches(0.3), Inches(0.3))
        except:
            pass
        
        # Label next to it
        tb = slide.shapes.add_textbox(Inches(1.1), Inches(y - 0.05), Inches(1.2), Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = freq
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = WHITE

    # Pyramid Tiers (Width varies to make it a pyramid shape)
    pyramid_tiers = [
        # (title, bullet_text, width, left_pos, bg_color, border_color, y_pos)
        ("Executive Steering Committee", "• Strategy & Vision  • Contracts & Investments\n• Transformation Roadmap  • Financial Oversight", 2.0, 2.5, RGBColor(15, 60, 50), GREEN_BORDER, 1.15),
        ("Operational Steering Committee", "• KPI Review  • Innovation & Automation\n• Risks & Compliance  • Workforce Strategy", 2.4, 2.3, RGBColor(10, 40, 70), BORDER_BLUE, 1.95),
        ("Program Management Review (PRM)", "• Service Performance  • Projects & Initiatives\n• Automation Pipeline  • Risk & Issue Review", 2.8, 2.1, RGBColor(50, 40, 15), GOLD, 2.75),
        ("Service Review (TRM) & Daily Stand-up", "• Incident & Problem Review  • Change & Capacity\n• Backlog & Priorities  • Service Health", 3.2, 1.9, RGBColor(40, 15, 45), RGBColor(160, 60, 160), 3.55)
    ]

    for title, desc, w, l, bg, border, y in pyramid_tiers:
        # Tier card
        draw_card(l, y, w, 0.72, bg, border, 1.5)
        
        # Text box inside tier card
        tb = slide.shapes.add_textbox(Inches(l + 0.1), Inches(y + 0.05), Inches(w - 0.2), Inches(0.62))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        
        p1 = tf.paragraphs[0]
        p1.alignment = PP_ALIGN.CENTER
        r1 = p1.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = GOLD
        
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = desc
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = WHITE

    # --- COLUMN 2: GOVERNANCE STRUCTURE ---
    # Box 1: Executive Steering
    draw_card(4.9, 1.15, 2.9, 0.4, CARD_BG, BORDER_BLUE)
    add_text_box(5.0, 1.22, 2.7, 0.3, [{"text": "Executive Steering Committee", "bold": True, "size": 9, "color": WHITE}], PP_ALIGN.CENTER)
    draw_connector_line(6.35, 1.55, 0.02, 0.2, BORDER_BLUE)

    # Box 2: IT Operations Governance Board
    draw_card(4.9, 1.75, 2.9, 0.4, CARD_BG, BORDER_BLUE)
    add_text_box(5.0, 1.82, 2.7, 0.3, [{"text": "IT Operations Governance Board", "bold": True, "size": 9, "color": WHITE}], PP_ALIGN.CENTER)
    
    # Lines connecting to the 3 columns below
    draw_connector_line(6.35, 2.15, 0.02, 0.2, BORDER_BLUE)
    draw_connector_line(5.35, 2.35, 2.0, 0.02, BORDER_BLUE)
    draw_connector_line(5.35, 2.35, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(7.35, 2.35, 0.02, 0.15, BORDER_BLUE)
    
    # 3 Middle branches
    draw_card(4.9, 2.5, 0.9, 0.6, CARD_BG, BORDER_BLUE)
    add_text_box(4.92, 2.55, 0.86, 0.5, [{"text": "Service\nMgmt Gov", "bold": True, "size": 7.5, "color": CYAN}], PP_ALIGN.CENTER)
    
    draw_card(5.9, 2.5, 0.9, 0.6, CARD_BG, BORDER_BLUE)
    add_text_box(5.92, 2.55, 0.86, 0.5, [{"text": "Operations\nGovernance", "bold": True, "size": 7.5, "color": GOLD}], PP_ALIGN.CENTER)
    
    draw_card(6.9, 2.5, 0.9, 0.6, CARD_BG, BORDER_BLUE)
    add_text_box(6.92, 2.55, 0.86, 0.5, [{"text": "CoE\n(Cross Func)", "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Connections to Program / Delivery Management
    draw_connector_line(5.35, 3.1, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(6.35, 3.1, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(7.35, 3.1, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(5.35, 3.25, 2.0, 0.02, BORDER_BLUE)
    draw_connector_line(6.35, 3.25, 0.02, 0.1, BORDER_BLUE)

    # Box 3: Program / Delivery Management
    draw_card(4.9, 3.35, 2.9, 0.4, CARD_BG, BORDER_BLUE)
    add_text_box(5.0, 3.42, 2.7, 0.3, [{"text": "Program / Delivery Management", "bold": True, "size": 9, "color": WHITE}], PP_ALIGN.CENTER)

    # Lines to Operations types
    draw_connector_line(6.35, 3.75, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(5.35, 3.9, 2.0, 0.02, BORDER_BLUE)
    draw_connector_line(5.35, 3.9, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(7.35, 3.9, 0.02, 0.1, BORDER_BLUE)

    # Infrastructure, Applications, Cloud Operations Cards
    draw_card(4.9, 4.0, 0.9, 0.5, CARD_BG, BORDER_BLUE)
    add_text_box(4.92, 4.05, 0.86, 0.4, [{"text": "Infra.\nOps", "bold": True, "size": 8, "color": WHITE}], PP_ALIGN.CENTER)
    
    draw_card(5.9, 4.0, 0.9, 0.5, CARD_BG, BORDER_BLUE)
    add_text_box(5.92, 4.05, 0.86, 0.4, [{"text": "Apps\nOps", "bold": True, "size": 8, "color": WHITE}], PP_ALIGN.CENTER)
    
    draw_card(6.9, 4.0, 0.9, 0.5, CARD_BG, BORDER_BLUE)
    add_text_box(6.92, 4.05, 0.86, 0.4, [{"text": "Cloud & Sec.\nOps", "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Delivery Teams
    draw_connector_line(5.35, 4.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(6.35, 4.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(7.35, 4.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(5.35, 4.6, 2.0, 0.02, BORDER_BLUE)
    draw_connector_line(6.35, 4.6, 0.02, 0.1, BORDER_BLUE)

    # Box 4: Delivery Teams
    draw_card(4.9, 4.7, 2.9, 0.35, CARD_BG, BORDER_BLUE)
    add_text_box(5.0, 4.75, 2.7, 0.25, [{"text": "Delivery Teams", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.CENTER)

    # --- COLUMN 3: CENTER OF EXCELLENCE (CoE) ---
    draw_card(8.0, 1.15, 2.6, 3.4, CARD_BG, BORDER_BLUE)
    
    coe_data = [
        ("PROCESS EXCELLENCE", "• ITIL Governance  • Change & Problem\n• Incident Standards  • Service Optimization", "icon_plm.png", 1.25),
        ("AUTOMATION & AI", "• Automation Strategy  • AIOps\n• RPA Opportunities  • Self-Healing", "icon_robot.png", 1.9),
        ("KPI & ANALYTICS", "• KPI Framework  • SLA Monitoring\n• Dashboards & Reports  • Predictive", "icon_scada.png", 2.55),
        ("CONTINUOUS IMPROVEMENT", "• CSI Program  • Process Optimization\n• Knowledge Mgmt  • Best Practices", "icon_devsecops.png", 3.2),
        ("TECHNOLOGY STANDARDS", "• Tool Standards  • Configuration Standards\n• Cloud & Security  • Operational Controls", "icon_quality.png", 3.85)
    ]

    for title, desc, icon_file, y in coe_data:
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.15), Inches(y), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = WHITE
        circ.line.fill.background()
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(8.2), Inches(y + 0.03), Inches(0.25), Inches(0.25))
        except:
            pass
            
        # Text details next to it
        tb = slide.shapes.add_textbox(Inches(8.55), Inches(y - 0.05), Inches(2.0), Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = GOLD
        
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = desc
        r2.font.size = Pt(7)
        r2.font.color.rgb = TEXT_MUTED

    # --- COLUMN 4: MEETING CADENCE ---
    meetings_data = [
        ("EXECUTIVE STEERING", "Annual / Bi-Annual\nStrategy, Investments, Contracts,\nRoadmap, Financial Review", 1.15),
        ("OPERATIONAL STEERING", "Quarterly\nKPI Review, Innovation, Risks,\nWorkforce, Compliance", 1.8),
        ("PROGRAM REVIEW (PRM)", "Monthly\nService Performance, Projects,\nAutomation, Risks & Issues", 2.45),
        ("SERVICE REVIEW (TRM)", "Weekly\nIncident Trends, Changes, Capacity,\nProblems, Improvement Actions", 3.1),
        ("DAILY STAND-UP", "Daily\nService Health, Major Incidents,\nBacklog, Priorities", 3.75)
    ]

    for title, desc, y in meetings_data:
        draw_card(10.7, y, 2.2, 0.6, CARD_BG, BORDER_BLUE)
        
        tb = slide.shapes.add_textbox(Inches(10.8), Inches(y + 0.05), Inches(2.0), Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        
        p1 = tf.paragraphs[0]
        r1 = p1.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = CYAN
        
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = desc
        r2.font.size = Pt(7)
        r2.font.color.rgb = WHITE

    # --- BOTTOM ROW ---
    # 1. RACI Matrix Card (Bottom-Left)
    draw_card(0.4, 4.65, 4.2, 2.15, CARD_BG, BORDER_BLUE)
    
    # RACI Title Header inside shape
    add_text_box(0.5, 4.7, 4.0, 0.25, [{"text": "RACI MATRIX (Key Activities)", "bold": True, "size": 10, "color": GOLD}], PP_ALIGN.CENTER)
    
    # Draw RACI Table manually
    raci_rows = [
        ("ACTIVITY", "SC", "OGB", "CoE", "DM", "OL"),
        ("IT Strategy", "A", "R", "C", "I", "I"),
        ("SLA Governance", "I", "A", "R", "R", "C"),
        ("Service Review", "I", "A", "R", "R", "C"),
        ("Automation Prog.", "C", "A", "R", "C", "C"),
        ("Continuous Imp.", "I", "A", "R", "C", "C"),
        ("Incident Mgmt", "I", "C", "C", "A", "R"),
        ("Knowledge Mgmt", "I", "C", "A", "R", "R")
    ]
    
    for row_idx, row in enumerate(raci_rows):
        ry = 4.95 + row_idx * 0.18
        
        # Activity Text
        add_text_box(0.5, ry, 1.5, 0.18, [{"text": row[0], "bold": (row_idx==0), "size": 7.5, "color": GOLD if row_idx==0 else WHITE}])
        
        # RACI Badges for each role
        for col_idx in range(1, 6):
            cell = row[col_idx]
            cx = 2.0 + (col_idx - 1) * 0.48
            
            if row_idx == 0:
                # Role Header
                add_text_box(cx, ry, 0.45, 0.18, [{"text": cell, "bold": True, "size": 7.5, "color": CYAN}], PP_ALIGN.CENTER)
            else:
                # Colored badges
                badge_bg = GREEN_BORDER if cell == "A" else (BORDER_BLUE if cell == "R" else (GOLD if cell == "C" else RGBColor(120, 50, 150)))
                circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.12), Inches(ry), Inches(0.18), Inches(0.18))
                circ.fill.solid()
                circ.fill.fore_color.rgb = badge_bg
                circ.line.fill.background()
                add_text_box(cx, ry - 0.02, 0.45, 0.18, [{"text": cell, "bold": True, "size": 7, "color": WHITE}], PP_ALIGN.CENTER)

    # RACI Legend at the very bottom of the card
    add_text_box(0.5, 6.6, 4.0, 0.15, [
        {"text": "A", "bold": True, "size": 7, "color": GREEN_BORDER}, {"text": " = Accountable   ", "size": 7, "color": WHITE},
        {"text": "R", "bold": True, "size": 7, "color": CYAN}, {"text": " = Responsible   ", "size": 7, "color": WHITE},
        {"text": "C", "bold": True, "size": 7, "color": GOLD}, {"text": " = Consulted   ", "size": 7, "color": WHITE},
        {"text": "I", "bold": True, "size": 7, "color": RGBColor(160, 60, 160)}, {"text": " = Informed", "size": 7, "color": WHITE}
    ], PP_ALIGN.CENTER)

    # 2. Key KPIs Managed by CoE (Bottom-Middle)
    draw_card(4.8, 4.65, 3.1, 2.15, CARD_BG, BORDER_BLUE)
    add_text_box(4.9, 4.7, 2.9, 0.25, [{"text": "KEY KPIs MANAGED BY CoE", "bold": True, "size": 10, "color": GOLD}], PP_ALIGN.CENTER)

    kpis_data = [
        ("SERVICE KPIs", "• SLA Compliance %  • Availability %  • MTTR\n• First Call Resolution  • Change Success Rate", "icon_sla.png", 4.95),
        ("OPERATIONS KPIs", "• Incident Volume  • Reopened Incidents\n• Problem Elimination Rate  • Automation Coverage", "icon_scada.png", 5.5),
        ("BUSINESS KPIs", "• CSAT  • Employee Experience  • Cost Reduction\n• Productivity Gain  • Service Availability", "icon_architecture.png", 6.05)
    ]
    for kpi_title, kpi_bullets, icon_file, ky in kpis_data:
        # Icon circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(4.95), Inches(ky), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = WHITE
        circ.line.fill.background()
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(5.0), Inches(ky + 0.03), Inches(0.25), Inches(0.25))
        except:
            pass
            
        # Bullet list text box next to icon
        tb = slide.shapes.add_textbox(Inches(5.38), Inches(ky - 0.05), Inches(2.4), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = kpi_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = CYAN
        
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = kpi_bullets
        r2.font.size = Pt(7)
        r2.font.color.rgb = WHITE

    # 3. CoE Organization (Bottom-Right)
    draw_card(8.0, 4.65, 4.9, 2.15, CARD_BG, BORDER_BLUE)
    add_text_box(8.1, 4.7, 4.7, 0.25, [{"text": "CoE ORGANIZATION", "bold": True, "size": 10, "color": GOLD}], PP_ALIGN.CENTER)

    # Top Box: Head of IT Operations CoE
    draw_card(9.4, 5.0, 2.1, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(9.5, 5.05, 1.9, 0.25, [{"text": "Head of IT Operations CoE", "bold": True, "size": 8.5, "color": WHITE}], PP_ALIGN.CENTER)
    
    # Connecting Lines for CoE Org Tree
    draw_connector_line(10.45, 5.35, 0.02, 0.15, BORDER_BLUE)
    draw_connector_line(8.55, 5.5, 3.8, 0.02, BORDER_BLUE)
    draw_connector_line(8.55, 5.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(9.8, 5.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(11.1, 5.5, 0.02, 0.1, BORDER_BLUE)
    draw_connector_line(12.35, 5.5, 0.02, 0.1, BORDER_BLUE)

    org_teams = [
        ("Process & ITIL\nGovernance", "icon_document.png", 8.1),
        ("Automation\n& AI", "icon_robot.png", 9.35),
        ("Reporting &\nAnalytics", "icon_scada.png", 10.6),
        ("Continuous Imp. &\nKnowledge Mgmt", "icon_lightbulb.png", 11.85)
    ]
    for team_title, team_icon, tx in org_teams:
        # Circular Icon
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(tx + 0.3), Inches(5.6), Inches(0.4), Inches(0.4))
        circ.fill.solid()
        circ.fill.fore_color.rgb = WHITE
        circ.line.color.rgb = BORDER_BLUE
        circ.line.width = Pt(1)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, team_icon), Inches(tx + 0.35), Inches(5.65), Inches(0.3), Inches(0.3))
        except:
            pass
            
        # Label box below
        add_text_box(tx, 6.05, 1.0, 0.6, [{"text": team_title, "bold": True, "size": 8, "color": WHITE}], PP_ALIGN.CENTER)

    # --- 4. BOTTOM-MOST BANNER (Horizontal Distribution with Separator Lines) ---
    banner_bg = draw_card(0.4, 6.9, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("STRATEGIC ALIGNMENT", "Aligned to Business Objectives", "icon_target.png", 0.4),
        ("OPERATIONAL EXCELLENCE", "Standardized Processes", "icon_excellence.png", 2.9),
        ("AUTOMATION FIRST", "Drive Efficiency & Reduce Cost", "icon_robot.png", 5.4),
        ("DATA DRIVEN DECISIONS", "Actionable Predictability", "icon_scada.png", 7.9),
        ("CONTINUOUS IMPROVEMENT", "Sustainable Value & Maturity", "icon_devsecops.png", 10.4)
    ]
    
    # Vertical separating lines
    draw_connector_line(2.9, 6.95, 0.02, 0.4, BORDER_BLUE)
    draw_connector_line(5.4, 6.95, 0.02, 0.4, BORDER_BLUE)
    draw_connector_line(7.9, 6.95, 0.02, 0.4, BORDER_BLUE)
    draw_connector_line(10.4, 6.95, 0.02, 0.4, BORDER_BLUE)

    for title, desc, icon_file, x_pos in footer_segments:
        # Icon
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.1), Inches(7.0), Inches(0.3), Inches(0.3))
        except:
            pass
            
        # Textbox next to icon
        tb = slide.shapes.add_textbox(Inches(x_pos + 0.45), Inches(6.95), Inches(2.0), Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = WHITE
        r1.font.name = "Roboto"
        
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(7)
        r2.font.color.rgb = CYAN
        r2.font.name = "Arial"


# ==========================================
# SLIDE 8 GENERATION
# ==========================================
def build_slide_8():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons"

    # 1. Slide Title
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "AKKODIS OFFSHORE DEVELOPMENT CENTER – PUNE, INDIA\n"
    r_t1.font.name = "Arial"
    r_t1.font.size = Pt(22)
    r_t1.font.bold = True
    r_t1.font.color.rgb = WHITE
    
    r_t2 = p_title.add_run()
    r_t2.text = "Engineering Excellence. Digital Innovation. Delivered for Global Mobility."
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = GOLD

    # Akkodis Logo
    logo_path = os.path.join(icons_dir, "logo_akkodis_white.png")
    try:
        slide.shapes.add_picture(logo_path, Inches(10.8), Inches(0.25), Inches(2.0), Inches(0.4))
    except Exception as e:
        print(f"Error adding logo: {e}")

    # --- SECTION 1: DEVELOPMENT CENTER OVERVIEW (Top-Left) ---
    draw_card(0.4, 0.9, 4.2, 3.6, CARD_BG, BORDER_BLUE)
    
    draw_card(0.4, 0.9, 4.2, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 0.95, 4.0, 0.25, [{"text": "1. DEVELOPMENT CENTER OVERVIEW", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Retain the provided building image
    building_img_path = os.path.join(icons_dir, "pune_building.png")
    if os.path.exists(building_img_path):
        try:
            slide.shapes.add_picture(building_img_path, Inches(0.55), Inches(1.35), Inches(1.6), Inches(1.8))
        except Exception as e:
            draw_card(0.55, 1.35, 1.6, 1.8, RGBColor(5, 15, 35), BORDER_BLUE)
            add_text_box(0.6, 2.1, 1.5, 0.4, [{"text": "[ Building Image ]", "size": 7.5, "color": TEXT_MUTED}], PP_ALIGN.CENTER)
    else:
        draw_card(0.55, 1.35, 1.6, 1.8, RGBColor(5, 15, 35), BORDER_BLUE)
        add_text_box(0.6, 2.1, 1.5, 0.4, [{"text": "[ Building Image ]", "size": 7.5, "color": TEXT_MUTED}], PP_ALIGN.CENTER)
    
    metadata = [
        ("Location", "Hinjewadi, Pune, India", "icon_marker_w.png", 1.35),
        ("Established", "2012", "icon_calendar_w.png", 1.8),
        ("Center Size", "650+ Professionals\nand growing", "icon_group_w.png", 2.25),
        ("Purpose", "Deliver high-quality engineering\nsolutions across Digital & Mechanical", "icon_target_w.png", 2.75)
    ]
    for m_title, m_desc, icon_file, my in metadata:
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(2.3), Inches(my), Inches(0.32), Inches(0.32))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(2.34), Inches(my + 0.04), Inches(0.24), Inches(0.24))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(2.7), Inches(my - 0.05), Inches(1.8), Inches(0.45))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = m_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = m_desc
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    draw_card(0.55, 3.25, 3.9, 1.15, CARD_BG, BORDER_BLUE)
    add_text_box(0.65, 3.3, 3.7, 0.25, [{"text": "Key Strengths", "bold": True, "size": 8.5, "color": CYAN}], PP_ALIGN.CENTER)
    
    strengths = [
        ("Domain\nExpertise", "icon_diploma_w.png", 0.6),
        ("Scalable\nTalent Pool", "icon_growth_group_w.png", 1.55),
        ("Global Delivery\nModel", "icon_globe_w.png", 2.5),
        ("Innovation\n& Quality", "icon_idea_w.png", 3.45)
    ]
    for s_title, s_icon, sx in strengths:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, s_icon), Inches(sx + 0.35), Inches(3.55), Inches(0.28), Inches(0.28))
        except:
            pass
        add_text_box(sx + 0.1, 3.9, 0.8, 0.45, [{"text": s_title, "bold": True, "size": 7, "color": WHITE}], PP_ALIGN.CENTER)

    # --- SECTION 2: PROJECT TEAM SIZE & ROLE DISTRIBUTION (Top-Middle) ---
    draw_card(4.8, 0.9, 4.2, 3.6, CARD_BG, BORDER_BLUE)
    
    draw_card(4.8, 0.9, 4.2, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(4.9, 0.95, 4.0, 0.25, [{"text": "2. PROJECT TEAM SIZE & ROLE DISTRIBUTION", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    chart_data = CategoryChartData()
    chart_data.categories = ['Software Engineers (30%)', 'Test Engineers (20%)', 'Mechanical Engineers (15%)', 'Project Managers (15%)', 'System / Integration (10%)', 'Design Engineers (10%)']
    chart_data.add_series('Roles', (30, 20, 15, 15, 10, 10))

    try:
        chart_shape = slide.shapes.add_chart(
            XL_CHART_TYPE.DOUGHNUT, Inches(4.9), Inches(1.3), Inches(4.0), Inches(2.2), chart_data
        )
        chart = chart_shape.chart
        chart.has_legend = True
        chart.legend.include_in_layout = False
        chart.legend.font.color.rgb = WHITE
        chart.legend.font.size = Pt(7.5)
        chart.legend.font.name = "Arial"
        
        chart.plots[0].has_data_labels = True
        data_labels = chart.plots[0].data_labels
        data_labels.font.color.rgb = WHITE
        data_labels.font.size = Pt(7.5)
        data_labels.font.name = "Arial"
    except Exception as e:
        print(f"Error adding doughnut chart: {e}")

    circ_center = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.55), Inches(2.1), Inches(0.55), Inches(0.55))
    circ_center.fill.solid()
    circ_center.fill.fore_color.rgb = CARD_BG
    circ_center.line.fill.background()
    add_text_box(6.55, 2.22, 0.55, 0.35, [{"text": "650+\nFTEs", "bold": True, "size": 7, "color": GOLD}], PP_ALIGN.CENTER)

    draw_card(4.95, 3.6, 3.9, 0.8, CARD_BG, BORDER_BLUE)
    add_text_box(5.05, 3.65, 3.7, 0.7, [
        {"text": "Key Roles:\n", "bold": True, "size": 8, "color": CYAN},
        {"text": "Developers | Test Engineers | Mechanical Engineers | System Engineers | Project Managers | Architects | DevOps Engineers | Design Engineers | Data Engineers | QA Leads", "size": 7, "color": WHITE}
    ], PP_ALIGN.CENTER)

    # --- SECTION 3: SYSTEM ACCESS LANDSCAPE (Top-Right) ---
    draw_card(9.2, 0.9, 3.7, 3.6, CARD_BG, BORDER_BLUE)
    
    draw_card(9.2, 0.9, 3.7, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(9.3, 0.95, 3.5, 0.25, [{"text": "3. SYSTEM ACCESS LANDSCAPE", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    add_text_box(9.3, 1.3, 3.5, 0.2, [{"text": "Secure Access to Customer Systems via VPN & SSO", "bold": True, "size": 8, "color": CYAN}], PP_ALIGN.CENTER)

    grid_items = [
        ("VOLKSWAGEN", "Requirements / ALM", "logo_vw.png", 0, 0),
        ("KOSTAL", "PDM & BOM", "logo_kostal.png", 1, 0),
        ("Jira", "Issue Tracking", "logo_jira.png", 2, 0),
        ("Confluence", "Documentation", "logo_confluence.png", 0, 1),
        ("SAP", "Finance Mgmt", "logo_sap.png", 1, 1),
        ("ServiceNow", "ITSM & Requests", "logo_servicenow.png", 2, 1),
        ("IBM DOORS", "Requirements", "logo_doors.png", 0, 2),
        ("Teamcenter", "PLM & ALM", "logo_teamcenter.png", 1, 2),
        ("GitLab", "Source Control", "logo_gitlab.png", 2, 2)
    ]
    for name, desc, logo_file, col, row in grid_items:
        gx = 9.35 + col * 1.15
        gy = 1.55 + row * 0.72
        gw = 1.1
        gh = 0.65
        
        draw_card(gx, gy, gw, gh, CARD_BG, BORDER_BLUE)
        
        logo_path = os.path.join(icons_dir, logo_file)
        if os.path.exists(logo_path):
            try:
                slide.shapes.add_picture(logo_path, Inches(gx + 0.1), Inches(gy + 0.05), Inches(gw - 0.2), Inches(0.35))
            except:
                add_text_box(gx, gy + 0.05, gw, 0.35, [{"text": name, "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)
        else:
            add_text_box(gx, gy + 0.05, gw, 0.35, [{"text": name, "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)
            
        add_text_box(gx, gy + 0.42, gw, 0.2, [{"text": desc, "size": 6.5, "color": TEXT_MUTED}], PP_ALIGN.CENTER)

    draw_card(9.35, 3.85, 3.4, 0.3, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(9.45, 3.9, 3.2, 0.2, [{"text": "Secure  |  Compliant  |  Monitored", "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)

    # --- SECTION 4: TOOLS & TECHNOLOGIES (Bottom-Left) ---
    draw_card(0.4, 4.6, 8.6, 2.15, CARD_BG, BORDER_BLUE)
    
    draw_card(0.4, 4.6, 8.6, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 4.65, 8.4, 0.25, [{"text": "4. TOOLS & TECHNOLOGIES", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    draw_card(0.5, 5.0, 3.7, 0.28, RGBColor(10, 50, 80), CYAN)
    add_text_box(0.5, 5.05, 3.7, 0.22, [{"text": "DIGITAL (SOFTWARE & ELECTRONICS)", "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)
    
    # 5 Digital columns
    digital_columns = [
        ("Languages", "C, C++, C#\nJava, Python\nKotlin, JS, SQL", 0.5, "icon_languages.png"),
        ("Frameworks", ".NET, Spring\nNode.js, React\nQt, AUTOSAR", 1.25, "icon_frameworks.png"),
        ("Tools", "VS Code, Eclipse\nIntelliJ, MATLAB\nSimulink, CANoe", 2.0, "icon_tools.png"),
        ("Testing", "vTESTstudio\nSelenium, JUnit\nPyTest, JMeter", 2.75, "icon_testing.png"),
        ("DevOps / CD", "GitLab CI, Docker\nJenkins, Nexus\nKubernetes", 3.5, "icon_devops.png")
    ]
    for d_title, d_text, dx, icon_file in digital_columns:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(dx + 0.22), Inches(5.35), Inches(0.26), Inches(0.26))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(dx), Inches(5.65), Inches(0.7), Inches(0.65))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run()
        r1.text = d_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = CYAN
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = d_text
        r2.font.size = Pt(6.5)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    draw_connector_line(4.35, 5.0, 0.015, 1.25, BORDER_BLUE)

    draw_card(4.45, 5.0, 4.45, 0.28, RGBColor(15, 60, 30), GREEN_BORDER)
    add_text_box(4.45, 5.05, 4.45, 0.22, [{"text": "MECHANICAL (DESIGN & ENGINEERING)", "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)
    
    # 4 Mechanical columns
    mech_columns = [
        ("CAD Tools", "CATIA V5/V6\nNX, Creo\nSolidWorks\nInventor", 4.45, "icon_cad.png"),
        ("CAE / Simulation", "ANSYS\nAbaqus\nAdams\nSimcenter", 5.55, "icon_cae.png"),
        ("PLM / Data Mgmt", "Teamcenter\nENOVIA\nWindchill\nVault", 6.65, "icon_plm_db.png"),
        ("Documentation", "MS Office\nConfluence\nSharePoint", 7.75, "icon_doc.png")
    ]
    for m_title, m_text, mx, icon_file in mech_columns:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(mx + 0.35), Inches(5.35), Inches(0.26), Inches(0.26))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(mx), Inches(5.65), Inches(1.0), Inches(0.65))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run()
        r1.text = m_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GREEN_BORDER
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = m_text
        r2.font.size = Pt(6.5)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    draw_card(0.5, 6.35, 8.4, 0.3, CARD_BG, BORDER_BLUE)
    add_text_box(0.6, 6.4, 8.2, 0.2, [{"text": "Agile  |  Automation  |  Continuous Improvement  |  Quality by Design", "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)

    # --- SECTION 5: COLLABORATION MODEL (Bottom-Right) ---
    draw_card(9.2, 4.6, 3.7, 2.15, CARD_BG, BORDER_BLUE)
    
    draw_card(9.2, 4.6, 3.7, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(9.3, 4.65, 3.5, 0.25, [{"text": "5. COLLABORATION MODEL", "bold": True, "size": 10.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Background world map with minimum transparency
    map_path = os.path.join(icons_dir, "world_map.png")
    if os.path.exists(map_path):
        try:
            slide.shapes.add_picture(map_path, Inches(9.25), Inches(5.0), Inches(3.6), Inches(1.3))
        except:
            pass

    # Diagram nodes
    draw_card(9.35, 5.05, 0.9, 0.45, CARD_BG, BORDER_BLUE)
    add_text_box(9.35, 5.1, 0.9, 0.35, [{"text": "VW Group\nGlobal Teams", "bold": True, "size": 7, "color": WHITE}], PP_ALIGN.CENTER)
    
    draw_connector_line(10.3, 5.25, 0.2, 0.02, CYAN)
    draw_connector_line(11.5, 5.25, 0.2, 0.02, CYAN)
    
    draw_card(10.55, 5.0, 0.9, 0.55, RGBColor(12, 35, 75), GOLD)
    add_text_box(10.55, 5.05, 0.9, 0.45, [{"text": "Akkodis\nODC Pune", "bold": True, "size": 7.5, "color": GOLD}], PP_ALIGN.CENTER)
    
    draw_card(11.75, 5.05, 0.9, 0.45, CARD_BG, BORDER_BLUE)
    add_text_box(11.75, 5.1, 0.9, 0.35, [{"text": "Other WW\nLocations", "bold": True, "size": 7, "color": WHITE}], PP_ALIGN.CENTER)

    col_items = [
        ("Aligned\nProcesses", "icon_process_w.png", 9.25),
        ("Agile & Scalable\nDelivery", "icon_workflow_w.png", 10.15),
        ("Transparent\nComm.", "icon_chat_w.png", 11.05),
        ("High Quality\n& Innovation", "icon_star_w.png", 11.95)
    ]
    for title, icon_file, cx in col_items:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.25), Inches(5.62), Inches(0.24), Inches(0.24))
        except:
            pass
        add_text_box(cx + 0.05, 5.92, 0.7, 0.35, [{"text": title, "bold": True, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # --- 6. BOTTOM-MOST BANNER ---
    banner_bg = draw_card(0.4, 6.85, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("Security First", "icon_shield_w.png"),
        ("People & Culture", "icon_group_w.png"),
        ("Quality Driven", "icon_badge_w.png"),
        ("Innovation Led", "icon_rocket_w.png"),
        ("One Akkodis", "icon_network_w.png")
    ]
    
    slot_w = 12.53 / 6.0
    for idx, (title, icon_file) in enumerate(footer_segments):
        x_pos = 0.4 + idx * slot_w
        
        if idx > 0:
            draw_connector_line(x_pos, 6.9, 0.02, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.15), Inches(6.95), Inches(0.3), Inches(0.3))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(x_pos + 0.5), Inches(6.92), Inches(slot_w - 0.5), Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = WHITE
        r1.font.name = "Arial"

    x_ft = 0.4 + 5 * slot_w
    draw_connector_line(x_ft, 6.9, 0.02, 0.4, BORDER_BLUE)
    
    tb_ft = slide.shapes.add_textbox(Inches(x_ft + 0.1), Inches(6.92), Inches(slot_w - 0.2), Inches(0.4))
    tf_ft = tb_ft.text_frame
    tf_ft.word_wrap = True
    tf_ft.margin_left = tf_ft.margin_right = tf_ft.margin_top = tf_ft.margin_bottom = 0
    p_ft = tf_ft.paragraphs[0]
    p_ft.alignment = PP_ALIGN.RIGHT
    r_ft = p_ft.add_run()
    r_ft.text = "Engineering a Smarter Future Together"
    r_ft.font.bold = True
    r_ft.font.size = Pt(9.5)
    r_ft.font.name = "Arial"



# ==========================================
# SLIDE 9 GENERATION
# ==========================================
def build_slide_9():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04  # Minimal rounded corner (~4px look)
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "NPDM TRAINING FOR NEW RESOURCES\n"
    r_t1.font.name = "Arial"
    r_t1.font.size = Pt(22)
    r_t1.font.bold = True
    r_t1.font.color.rgb = WHITE
    
    r_t2 = p_title.add_run()
    r_t2.text = "Ensuring every resource is NPDM-ready before contributing to our projects"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = GOLD

    # Akkodis Logo
    logo_path = os.path.join(icons_dir, "logo_akkodis_white.png")
    try:
        slide.shapes.add_picture(logo_path, Inches(10.8), Inches(0.25), Inches(2.0), Inches(0.4))
    except:
        pass

    # --- TOP SECTION: Overview & Training Expert ---
    # Left Card: Overview (expanded vertically to 2.5)
    draw_card(0.4, 0.9, 5.8, 2.5, CARD_BG, BORDER_BLUE)
    cal_path = os.path.join(icons_dir, "slide9_calendar_gen.png")
    if os.path.exists(cal_path):
        try:
            slide.shapes.add_picture(cal_path, Inches(0.65), Inches(1.2), Inches(1.4), Inches(1.4))
        except:
            pass
            
    add_text_box(2.2, 1.25, 3.8, 1.8, [
        {"text": "NPDM training for all\nnew resources must be\ncompleted within\n", "size": 11.5, "color": WHITE},
        {"text": "10 WORKING DAYS\n", "bold": True, "size": 14, "color": CYAN},
        {"text": "before they are assigned\nto a project.", "size": 11.5, "color": WHITE}
    ])

    # Right Card: Training Expert (expanded vertically to 2.5)
    draw_card(6.4, 0.9, 6.5, 2.5, CARD_BG, BORDER_BLUE)
    
    # Separator Line Header
    draw_connector_line(6.6, 1.05, 6.1, 0.015, BORDER_BLUE)
    tb_header = slide.shapes.add_textbox(Inches(7.8), Inches(0.95), Inches(3.7), Inches(0.25))
    tb_header.text_frame.word_wrap = True
    tb_header.text_frame.margin_left = tb_header.text_frame.margin_right = tb_header.text_frame.margin_top = tb_header.text_frame.margin_bottom = 0
    p_h = tb_header.text_frame.paragraphs[0]
    p_h.alignment = PP_ALIGN.CENTER
    r_h = p_h.add_run()
    r_h.text = " TRAINING BY EXPERIENCED EXPERT "
    r_h.font.bold = True
    r_h.font.size = Pt(8.5)
    r_h.font.color.rgb = CYAN
    r_h.font.name = "Arial"
    
    # Circle trainer image
    trainer_path = os.path.join(icons_dir, "slide9_trainer_gen.png")
    if os.path.exists(trainer_path):
        try:
            slide.shapes.add_picture(trainer_path, Inches(6.6), Inches(1.25), Inches(1.6), Inches(1.6))
        except:
            pass
            
    # Trained details on the right
    # Row 1: Trained by France CoE
    c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.45), Inches(1.3), Inches(0.35), Inches(0.35))
    c1.fill.solid()
    c1.fill.fore_color.rgb = RGBColor(12, 35, 75)
    c1.line.color.rgb = CYAN
    c1.line.width = Pt(0.7)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_diploma_w.png"), Inches(8.5), Inches(1.35), Inches(0.25), Inches(0.25))
    except:
        pass
        
    add_text_box(8.9, 1.27, 3.8, 0.45, [
        {"text": "Trained by\n", "size": 8.5, "color": WHITE},
        {"text": "France CoE ", "bold": True, "size": 9.5, "color": GOLD},
        {"text": "(Center of Excellence)", "size": 8.5, "color": WHITE}
    ])

    # Row 2: Has prior Renault Project Experience
    c2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.45), Inches(1.9), Inches(0.35), Inches(0.35))
    c2.fill.solid()
    c2.fill.fore_color.rgb = RGBColor(12, 35, 75)
    c2.line.color.rgb = CYAN
    c2.line.width = Pt(0.7)
    try:
        # Load Renault logo directly
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_renault.png"), Inches(8.5), Inches(1.95), Inches(0.25), Inches(0.25))
    except:
        pass
        
    add_text_box(8.9, 1.87, 3.8, 0.45, [
        {"text": "Has prior\n", "size": 8.5, "color": WHITE},
        {"text": "Renault ", "bold": True, "size": 9.5, "color": GOLD},
        {"text": "Project Experience", "size": 8.5, "color": WHITE}
    ])

    # --- MIDDLE SECTION: OUR APPROACH (shifted vertically to occupy space) ---
    draw_connector_line(0.4, 3.65, 12.5, 0.015, BORDER_BLUE)
    tb_app = slide.shapes.add_textbox(Inches(5.2), Inches(3.55), Inches(2.9), Inches(0.25))
    tb_app.text_frame.word_wrap = True
    tb_app.text_frame.margin_left = tb_app.text_frame.margin_right = tb_app.text_frame.margin_top = tb_app.text_frame.margin_bottom = 0
    p_app = tb_app.text_frame.paragraphs[0]
    p_app.alignment = PP_ALIGN.CENTER
    r_app = p_app.add_run()
    r_app.text = " OUR APPROACH "
    r_app.font.bold = True
    r_app.font.size = Pt(8.5)
    r_app.font.color.rgb = CYAN
    r_app.font.name = "Arial"

    # Flowchart: 5 columns
    # Replaced step 4 icon with icon_excellence.png (checklist/achievement look)
    flow_steps = [
        ("1. New Resource\nOnboarding", "icon_group_w.png", 0.4),
        ("2. NPDM Training\n(Classroom / Virtual)", "icon_process_w.png", 2.9),
        ("3. Complete Within\n10 WORKING DAYS", "icon_calendar_w.png", 5.4),
        ("4. Assessment &\nCompetency Validation", "icon_excellence.png", 7.9),
        ("5. Ready for Project\nAssignment", "icon_badge_w.png", 10.4)
    ]
    for idx, (title, icon_file, x_pos) in enumerate(flow_steps):
        # Circle icon background
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.65), Inches(3.9), Inches(0.8), Inches(0.8))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.8)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.9), Inches(4.15), Inches(0.3), Inches(0.3))
        except:
            pass
            
        if idx < 4:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x_pos + 1.85), Inches(4.2), Inches(0.35), Inches(0.2))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

        tb_step = slide.shapes.add_textbox(Inches(x_pos), Inches(4.85), Inches(2.1), Inches(0.75))
        tf_step = tb_step.text_frame
        tf_step.word_wrap = True
        tf_step.margin_left = tf_step.margin_right = tf_step.margin_top = tf_step.margin_bottom = 0
        p_step = tf_step.paragraphs[0]
        p_step.alignment = PP_ALIGN.CENTER
        
        if "10 WORKING DAYS" in title:
            r1 = p_step.add_run()
            r1.text = "3. Complete Within\n"
            r1.font.bold = True
            r1.font.size = Pt(8.5)
            r1.font.color.rgb = WHITE
            r1.font.name = "Arial"
            
            r2 = p_step.add_run()
            r2.text = "10 WORKING DAYS"
            r2.font.bold = True
            r2.font.size = Pt(9.5)
            r2.font.color.rgb = CYAN
            r2.font.name = "Arial"
        else:
            r1 = p_step.add_run()
            r1.text = title
            r1.font.bold = True
            r1.font.size = Pt(8.5)
            r1.font.color.rgb = WHITE
            r1.font.name = "Arial"

    # --- BOTTOM SECTION: KEY BENEFITS (shifted and expanded to height 1.0) ---
    # Left Header badge
    draw_card(0.4, 5.75, 1.4, 1.0, RGBColor(12, 35, 75), GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_star_w.png"), Inches(0.95), Inches(5.85), Inches(0.3), Inches(0.3))
    except:
        pass
    add_text_box(0.4, 6.27, 1.4, 0.35, [{"text": "KEY\nBENEFITS", "bold": True, "size": 8.5, "color": GOLD}], PP_ALIGN.CENTER)

    # Right Card container
    draw_card(1.9, 5.75, 11.0, 1.0, CARD_BG, BORDER_BLUE)
    
    # Replaced target icon with icon_quality.png (quality/target look)
    benefit_cols = [
        ("Ensures adherence\nto NPDM standards\nfrom day one", "icon_shield_w.png", 1.9),
        ("Improves quality\nand data\nconsistency", "icon_quality.png", 4.65),
        ("Faster onboarding\nand effective\ncontribution", "icon_group_w.png", 7.4),
        ("Stronger project\nexecution and\npredictable results", "icon_rocket_w.png", 10.15)
    ]
    for idx, (b_text, icon_file, bx) in enumerate(benefit_cols):
        if idx > 0:
            draw_connector_line(bx, 5.8, 0.015, 0.9, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(bx + 0.15), Inches(6.1), Inches(0.3), Inches(0.3))
        except:
            pass
            
        add_text_box(bx + 0.55, 5.9, 2.1, 0.7, [{"text": b_text, "size": 7.5, "color": WHITE}])

    # --- 6. BOTTOM-MOST BANNER ---
    draw_connector_line(0.4, 6.85, 12.5, 0.015, BORDER_BLUE)
    
    tb_ft1 = slide.shapes.add_textbox(Inches(0.4), Inches(6.92), Inches(5.5), Inches(0.4))
    tf_ft1 = tb_ft1.text_frame
    tf_ft1.word_wrap = True
    tf_ft1.margin_left = tf_ft1.margin_right = tf_ft1.margin_top = tf_ft1.margin_bottom = 0
    p_ft1 = tf_ft1.paragraphs[0]
    r_ft1 = p_ft1.add_run()
    r_ft1.text = "Right Training. Right Start. Right Impact."
    r_ft1.font.bold = True
    r_ft1.font.size = Pt(9.5)
    r_ft1.font.color.rgb = GOLD
    r_ft1.font.name = "Arial"

    tb_ft2 = slide.shapes.add_textbox(Inches(7.4), Inches(6.92), Inches(5.5), Inches(0.4))
    tf_ft2 = tb_ft2.text_frame
    tf_ft2.word_wrap = True
    tf_ft2.margin_left = tf_ft2.margin_right = tf_ft2.margin_top = tf_ft2.margin_bottom = 0
    p_ft2 = tf_ft2.paragraphs[0]
    p_ft2.alignment = PP_ALIGN.RIGHT
    r_ft2 = p_ft2.add_run()
    r_ft2.text = "NPDM Excellence, Delivered."
    r_ft2.font.bold = True
    r_ft2.font.size = Pt(9.5)
    r_ft2.font.name = "Arial"



# ==========================================
# SLIDE 10 GENERATION
# ==========================================
def build_slide_10():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04  # Minimal rounded corner (~4px look)
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "INDUSTRIAL DIGITALIZATION EXPERTISE\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "Accelerating Airbus Smart Factory & Digital Operations Transformation"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus_plane.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # Introduction paragraph (Arial, min font size 8/9)
    add_text_box(0.4, 0.92, 9.5, 0.45, [
        {"text": "Akkodis brings 15+ years of Airbus Digital Operations (DO) Shopfloor experience, supporting Operations, Quality, Procurement, Industrial Solutions and Aerostructures domains through engineering, analytics, automation and operational excellence services.", "size": 8.5, "color": WHITE}
    ])

    # --- 5 CARD COLUMNS + BUSINESS VALUE CARD ---
    col_w = 1.9
    spacing = 0.14
    
    # Columns details
    cols_data = [
        ("1. SMART MANUFACTURING\n& SHOPFLOOR DIGITALIZATION", [
            "Manufacturing Operations\nManagement (MOM)",
            "Digital Shopfloor Applications",
            "Production Line Enablement",
            "Industrial Asset Management",
            "Quality Inspection Digitization",
            "Connected Worker Solutions"
        ], "slide10_worker_tablet.png", 0),
        
        ("2. IT / OT INTEGRATION", [
            "SCADA Integration",
            "Industrial Data Streaming",
            "Edge-to-Cloud Connectivity",
            "Real-Time Manufacturing\nVisibility",
            "Production Data Consolidation",
            "Operational Monitoring & Control"
        ], "DIAGRAM", 1),
        
        ("3. DATA, ANALYTICS\n& SKYWISE", [
            "Skywise Application\nDevelopment",
            "Data Engineering & Pipeline\nDevelopment",
            "Manufacturing Performance\nAnalytics",
            "Predictive Maintenance\nAnalytics",
            "Real-Time KPI Dashboards",
            "Data Governance & Decision\nSupport"
        ], "slide10_dashboard.png", 2),
        
        ("4. AUTOMATION &\nINDUSTRY 4.0", [
            "Robotics & Industrial\nAutomation",
            "RPA & Workflow Automation",
            "AI-Assisted Operations",
            "Event-Driven Architectures\n(Kafka)",
            "Digital Process Optimization",
            "Intelligent Operational Support"
        ], "slide10_robotic_arm.png", 3),
        
        ("5. AUGMENTED\nWORKER SOLUTIONS", [
            "AR/VR Platforms for\nShopfloor Operations",
            "HoloLens-Based Inspection\nSolutions",
            "Digital Work Instructions",
            "Mixed Reality Manufacturing\nSupport",
            "Connected Wearable\nTechnologies",
            "Digital Quality & Compliance\nValidation"
        ], "slide10_ar_worker.png", 4)
    ]

    for title, bullet_list, img_file, col_idx in cols_data:
        x_pos = 0.4 + col_idx * (col_w + spacing)
        
        # Outer Card
        draw_card(x_pos, 1.42, col_w, 4.1, CARD_BG, BORDER_BLUE)
        
        # Header block inside card
        draw_card(x_pos, 1.42, col_w, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
        add_text_box(x_pos, 1.46, col_w, 0.3, [{"text": title, "bold": True, "size": 7, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Bullets
        bullets_text = ""
        for b in bullet_list:
            bullets_text += "•  " + b + "\n"
        bullets_text = bullets_text.strip("\n")
        add_text_box(x_pos + 0.06, 1.82, col_w - 0.12, 1.3, [{"text": bullets_text, "size": 7, "color": TEXT_MUTED}])

        # Bottom Graphic
        if img_file == "DIAGRAM":
            # Draw SCADA/EDGE/CLOUD diagram
            draw_card(x_pos + 0.1, 4.65, 0.5, 0.22, CARD_BG, BORDER_BLUE)
            add_text_box(x_pos + 0.1, 4.68, 0.5, 0.18, [{"text": "SCADA", "bold": True, "size": 5.5, "color": WHITE}], PP_ALIGN.CENTER)
            
            draw_connector_line(x_pos + 0.6, 4.75, 0.12, 0.015, CYAN)
            
            draw_card(x_pos + 0.72, 4.65, 0.48, 0.22, CARD_BG, BORDER_BLUE)
            add_text_box(x_pos + 0.72, 4.68, 0.48, 0.18, [{"text": "EDGE", "bold": True, "size": 5.5, "color": WHITE}], PP_ALIGN.CENTER)
            
            draw_connector_line(x_pos + 1.2, 4.75, 0.12, 0.015, CYAN)
            
            draw_card(x_pos + 1.32, 4.65, 0.48, 0.22, RGBColor(12, 35, 75), CYAN)
            add_text_box(x_pos + 1.32, 4.68, 0.48, 0.18, [{"text": "CLOUD", "bold": True, "size": 5.5, "color": CYAN}], PP_ALIGN.CENTER)
            
            # Sub-text
            add_text_box(x_pos + 0.05, 5.1, col_w - 0.1, 0.35, [{"text": "Real-Time Shopfloor Data Pipeline", "size": 6.5, "color": GOLD}], PP_ALIGN.CENTER)
        else:
            try:
                slide.shapes.add_picture(os.path.join(icons_dir, img_file), Inches(x_pos + 0.08), Inches(4.35), Inches(col_w - 0.16), Inches(1.1))
            except:
                pass

    # Column 6: Business Value Delivered Card
    x_val = 0.4 + 5 * (col_w + spacing)
    draw_card(x_val, 1.42, col_w, 4.1, CARD_BG, CYAN)
    draw_card(x_val, 1.42, col_w, 0.35, RGBColor(12, 50, 60), CYAN)
    add_text_box(x_val, 1.46, col_w, 0.3, [{"text": "BUSINESS VALUE\nDELIVERED TO AIRBUS", "bold": True, "size": 7, "color": CYAN}], PP_ALIGN.CENTER)

    values = [
        "Faster Industrial Digital\nTransformation",
        "Increased Production\nVisibility & Control",
        "Improved Quality &\nOperational Efficiency",
        "Enhanced Connected\nWorker Experience",
        "Data-Driven Manufacturing\nDecisions",
        "Reduced Manual Effort\nThrough Automation",
        "Accelerated Smart Factory\nAdoption"
    ]
    for idx, val in enumerate(values):
        y_pos = 1.82 + idx * 0.5
        # Circle badge
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_val + 0.08), Inches(y_pos + 0.02), Inches(0.18), Inches(0.18))
        circ.fill.solid()
        circ.fill.fore_color.rgb = GREEN_BORDER
        circ.line.fill.background()
        
        # Check icon label
        add_text_box(x_val + 0.08, y_pos, 0.18, 0.18, [{"text": "✔", "bold": True, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)
        # Value text description
        add_text_box(x_val + 0.3, y_pos - 0.02, col_w - 0.35, 0.45, [{"text": val, "size": 7, "color": WHITE}])

    # --- PROVEN AIRBUS EXPERIENCE (Bottom-Middle Section) ---
    draw_connector_line(0.4, 5.62, 12.5, 0.015, BORDER_BLUE)
    tb_proven = slide.shapes.add_textbox(Inches(5.0), Inches(5.52), Inches(3.3), Inches(0.25))
    p_proven = tb_proven.text_frame.paragraphs[0]
    p_proven.alignment = PP_ALIGN.CENTER
    r_proven = p_proven.add_run()
    r_proven.text = " PROVEN AIRBUS EXPERIENCE "
    r_proven.font.bold = True
    r_proven.font.size = Pt(8.5)
    r_proven.font.color.rgb = CYAN
    r_proven.font.name = "Arial"

    # Shopfloor stats column
    tb_stats = slide.shapes.add_textbox(Inches(0.4), Inches(5.82), Inches(2.9), Inches(0.9))
    tf_stats = tb_stats.text_frame
    tf_stats.word_wrap = True
    tf_stats.margin_left = tf_stats.margin_right = tf_stats.margin_top = tf_stats.margin_bottom = 0
    p_stats = tf_stats.paragraphs[0]
    r_s_title = p_stats.add_run()
    r_s_title.text = "AIRBUS DIGITAL OPERATIONS\n(DO) SHOPFLOOR\n"
    r_s_title.font.bold = True
    r_s_title.font.size = Pt(8)
    r_s_title.font.color.rgb = GOLD
    r_s_title.font.name = "Arial"
    
    r_s_body = p_stats.add_run()
    r_s_body.text = "•  600+ Applications Managed\n•  100+ Critical Applications\n•  10,000+ Tickets Managed Annually\n•  Support Across France, Germany, UK & Spain\n•  Build, Run & Transform Delivery Model"
    r_s_body.font.size = Pt(7)
    r_s_body.font.color.rgb = WHITE
    r_s_body.font.name = "Arial"

    # Skywise column
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_skywise.png"), Inches(3.4), Inches(5.82), Inches(0.35), Inches(0.35))
    except:
        pass
        
    tb_sky = slide.shapes.add_textbox(Inches(3.85), Inches(5.82), Inches(2.7), Inches(0.9))
    tf_sky = tb_sky.text_frame
    tf_sky.word_wrap = True
    tf_sky.margin_left = tf_sky.margin_right = tf_sky.margin_top = tf_sky.margin_bottom = 0
    p_sky = tf_sky.paragraphs[0]
    r_sk_title = p_sky.add_run()
    r_sk_title.text = "AIRBUS SKYWISE EXPERTISE\n"
    r_sk_title.font.bold = True
    r_sk_title.font.size = Pt(8)
    r_sk_title.font.color.rgb = GOLD
    r_sk_title.font.name = "Arial"
    
    r_sk_body = p_sky.add_run()
    r_sk_body.text = "•  PySpark & Data Pipeline Development\n•  Slate Application Development\n•  Predictive Analytics Solutions\n•  Legacy-to-Skywise Migration\n•  End-to-End Data Engineering Support"
    r_sk_body.font.size = Pt(7)
    r_sk_body.font.color.rgb = WHITE
    r_sk_body.font.name = "Arial"

    # AR/VR column
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_arvr_headset.png"), Inches(6.6), Inches(5.82), Inches(0.35), Inches(0.35))
    except:
        pass
        
    tb_ar = slide.shapes.add_textbox(Inches(7.05), Inches(5.82), Inches(2.7), Inches(0.9))
    tf_ar = tb_ar.text_frame
    tf_ar.word_wrap = True
    tf_ar.margin_left = tf_ar.margin_right = tf_ar.margin_top = tf_ar.margin_bottom = 0
    p_ar = tf_ar.paragraphs[0]
    r_ar_title = p_ar.add_run()
    r_ar_title.text = "AIRBUS AR/VR & INDUSTRIAL SOLUTIONS\n"
    r_ar_title.font.bold = True
    r_ar_title.font.size = Pt(8)
    r_ar_title.font.color.rgb = GOLD
    r_ar_title.font.name = "Arial"
    
    r_ar_body = p_ar.add_run()
    r_ar_body.text = "•  MiRA Mixed Reality Platform\n•  HoloLens Inspection Solutions\n•  Smart Watch Enabled Shopfloor Solutions\n•  Connected Worker Initiatives\n•  Digital Inspection & Quality Programs"
    r_ar_body.font.size = Pt(7)
    r_ar_body.font.color.rgb = WHITE
    r_ar_body.font.name = "Arial"

    # Key Message Quote Box
    draw_card(9.8, 5.75, 3.1, 0.95, CARD_BG, BORDER_BLUE)
    
    # Quote Icon
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_chat_w.png"), Inches(9.88), Inches(5.82), Inches(0.24), Inches(0.24))
    except:
        pass
        
    add_text_box(10.2, 5.8, 2.65, 0.85, [
        {"text": "Akkodis combines Airbus domain knowledge, Skywise capabilities, Shopfloor digitalization experience, AR/VR innovation, and IT/OT integration know-how to support Airbus' journey towards Smart Manufacturing.", "size": 6.8, "color": WHITE}
    ])

    # --- 6. BOTTOM-MOST BANNER ---
    banner_bg = draw_card(0.4, 6.82, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("OUR DIFFERENTIATORS", "icon_excellence.png"),
        ("15+ Yrs Airbus Experience", "icon_diploma_w.png"),
        ("Dedicated Secure ODC", "icon_shield_w.png"),
        ("Airbus Governance", "icon_process_w.png"),
        ("AI & Automation", "icon_rocket_w.png"),
        ("24x7 Operations", "icon_calendar_w.png")
    ]
    
    slot_w = 12.53 / 6.0
    for idx, (title, icon_file) in enumerate(footer_segments):
        x_pos = 0.4 + idx * slot_w
        
        # Draw separators
        if idx > 0:
            draw_connector_line(x_pos, 6.87, 0.015, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.12), Inches(6.92), Inches(0.28), Inches(0.28))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(x_pos + 0.45), Inches(6.88), Inches(slot_w - 0.5), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GOLD if idx == 0 else WHITE
        r1.font.name = "Arial"



# ==========================================
# SLIDE 11 GENERATION
# ==========================================
def build_slide_11():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "BUNDLE UNDERSTANDING & DIGITAL OPERATIONS\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "Aligning Airbus Digital Operations Vision with a Scalable, Secure & Adaptive Delivery Model"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus_plane.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- LEFT COLUMN: Bundle Understanding & Digital India Bundle ---
    # Card 1: Bundle Understanding
    draw_card(0.4, 0.95, 7.8, 2.1, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 0.95, 7.8, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 1.0, 7.6, 0.25, [{"text": "BUNDLE UNDERSTANDING", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    bundle_items = [
        ("OPERATIONS", "Smart Factory\n& Shopfloor\nExcellence", "icon_company_w.png", 0.5),
        ("QUALITY", "Enterprise\nQuality\nTransformation", "icon_badge_w.png", 2.05),
        ("PROCUREMENT", "Digital\nProcurement\nExcellence", "icon_gear_w.png", 3.6),
        ("INDUSTRIAL SOLUTIONS", "Industrialization\n& Automation", "icon_process_w.png", 5.15),
        ("AEROSTRUCTURES", "End-to-End\nEngineering\nSolutions", "icon_globe_w.png", 6.7)
    ]
    for title, desc, icon_file, bx in bundle_items:
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(bx + 0.5), Inches(1.4), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(bx + 0.55), Inches(1.45), Inches(0.25), Inches(0.25))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(bx), Inches(1.8), Inches(1.35), Inches(1.15))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(7)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    # Card 2: Digital India Bundle
    draw_card(0.4, 3.2, 7.8, 2.35, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 3.2, 7.8, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 3.25, 7.6, 0.25, [{"text": "DIGITAL INDIA BUNDLE", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    wp_cols = [
        ("WP1 - DEVELOPMENT EXCELLENCE", [
            "SAFe", "Agile Scrum", "Waterfall", "DevSecOps & CI/CD", "Architecture", "Quality Engineering &\nTest Automation"
        ], 0.5, RGBColor(10, 50, 80), CYAN),
        
        ("WP2 - OPERATIONAL EXCELLENCE", [
            "Monitoring & Observability", "End-User Support", "Incident Management", "Problem Management", "Change & Release Management", "Maintenance &\nEnhancements", "Platform Services"
        ], 3.05, RGBColor(15, 60, 30), GREEN_BORDER),
        
        ("WP3 - GOVERNANCE EXCELLENCE", [
            "Release Management", "E2E Testing", "Architecture Consulting", "Problem Management", "Business Analysis", "Scrum / Agile Services"
        ], 5.6, RGBColor(12, 35, 75), GOLD)
    ]
    for wp_title, bullets, bx, header_bg, border_col in wp_cols:
        # Header block inside
        draw_card(bx, 3.65, 2.4, 0.26, header_bg, border_col)
        add_text_box(bx, 3.68, 2.4, 0.22, [{"text": wp_title, "bold": True, "size": 7, "color": border_col}], PP_ALIGN.CENTER)
        
        bullets_text = ""
        for b in bullets:
            bullets_text += "•  " + b + "\n"
        bullets_text = bullets_text.strip("\n")
        add_text_box(bx + 0.05, 3.98, 2.3, 1.45, [{"text": bullets_text, "size": 7, "color": WHITE}])

    # --- RIGHT COLUMN: Why Akkodis Differentiators ---
    draw_card(8.4, 0.95, 4.5, 4.6, CARD_BG, BORDER_BLUE)
    draw_card(8.4, 0.95, 4.5, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.5, 1.0, 4.3, 0.25, [{"text": "WHY AKKODIS - OUR DIFFERENTIATORS", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    diffs = [
        ("15+ Years Airbus DO Experience", "Deep domain and process knowledge", "icon_diploma_w.png"),
        ("600+ Airbus Applications Managed", "Across Operations, Quality & Procurement", "icon_group_w.png"),
        ("100+ Critical Applications", "Reliable support with high SLA", "icon_shield_w.png"),
        ("Skywise Expertise", "Data engineering, analytics and Skywise applications", "icon_skywise.png"),
        ("AR/VR & Connected Worker Solutions", "MiRA, HoloLens, Smart Wearables, IRIS Solutions", "icon_arvr_headset.png"),
        ("Build + Run + Transform Capability", "End-to-end ownership for predictable outcomes", "icon_workflow_w.png"),
        ("Dedicated Secure Airbus ODC", "Segregated, compliant and audit-ready delivery environment", "icon_shield_w.png")
    ]
    for idx, (d_title, d_desc, icon_file) in enumerate(diffs):
        y_pos = 1.4 + idx * 0.58
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.55), Inches(y_pos + 0.05), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(8.6), Inches(y_pos + 0.1), Inches(0.25), Inches(0.25))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(9.0), Inches(y_pos), Inches(3.8), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = d_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = d_desc
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    # --- BOTTOM SECTION: KEY MESSAGE BANNER ---
    draw_card(0.4, 5.75, 12.53, 0.9, CARD_BG, GOLD)
    
    # Left Key Message Box
    tb_msg = slide.shapes.add_textbox(Inches(0.5), Inches(5.8), Inches(7.5), Inches(0.8))
    tf_msg = tb_msg.text_frame
    tf_msg.word_wrap = True
    tf_msg.margin_left = tf_msg.margin_right = tf_msg.margin_top = tf_msg.margin_bottom = 0
    p_msg = tf_msg.paragraphs[0]
    r_msg = p_msg.add_run()
    r_msg.text = "KEY MESSAGE: Akkodis combines Airbus domain expertise, industrial digitalization know-how, operational excellence, and a scalable secure delivery model to rapidly adapt to evolving Airbus priorities while ensuring quality, security, and delivery predictability."
    r_msg.font.bold = True
    r_msg.font.size = Pt(8)
    r_msg.font.color.rgb = GOLD
    r_msg.font.name = "Arial"

    # Vertical Separator Line
    draw_connector_line(8.1, 5.8, 0.015, 0.8, BORDER_BLUE)

    # 4 Differentiators icons on the right
    diff_items = [
        ("INDUSTRY 4.0", "icon_excellence.png", 8.25),
        ("AI & ANALYTICS", "icon_rocket_w.png", 9.35),
        ("SECURE & COMPLIANT", "icon_shield_w.png", 10.45),
        ("PEOPLE & PARTNERSHIP", "icon_group_w.png", 11.55)
    ]
    for title, icon_file, cx in diff_items:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.35), Inches(5.82), Inches(0.24), Inches(0.24))
        except:
            pass
        add_text_box(cx, 6.22, 0.95, 0.35, [{"text": title, "bold": True, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Footer banner
    draw_connector_line(0.4, 6.8, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.88, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.88, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


# ==========================================
# SLIDE 12 GENERATION
# ==========================================
def build_slide_12():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "ADAPTABILITY & VALUE OUTCOMES\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "A Scalable, Secure & Adaptive Delivery Model Supporting Airbus Smart Factory"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus_plane.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- LEFT COLUMN: Hot Topics We Understand (2x4 Grid) ---
    draw_card(0.4, 0.95, 6.0, 4.6, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 0.95, 6.0, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 1.0, 5.8, 0.25, [{"text": "HOT TOPICS WE UNDERSTAND", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    hot_topics = [
        ("DIGITAL\nTRANSFORMATION", "Accelerate smart factory and industrial digitalization", "icon_excellence.png", 0, 0),
        ("AGILE\nAT SCALE", "Improve delivery predictability across ARTs", "icon_group_w.png", 1, 0),
        ("DEVSECOPS &\nAUTOMATION", "Industrialize CI/CD and security controls", "icon_rocket_w.png", 2, 0),
        ("CLOUD &\nOPENSHIFT", "Enable scalable, resilient and modern platforms", "icon_cloud.png", 3, 0),
        ("DATA, ANALYTICS\n& AI", "Data-driven operational decisions", "icon_process_w.png", 0, 1),
        ("SECURITY &\nCOMPLIANCE", "GDPR, Export Control, Secure-by-Design", "icon_shield_w.png", 1, 1),
        ("OPERATIONAL\nEXCELLENCE", "Availability, MTTR, SLA and customer satisfaction", "icon_gear_w.png", 2, 1),
        ("KNOWLEDGE &\nCONTINUITY", "Low-risk transition and knowledge retention", "icon_diploma_w.png", 3, 1)
    ]
    for title, desc, icon_file, col, row in hot_topics:
        gx = 0.55 + col * 1.42
        gy = 1.45 + row * 2.0
        
        # Sub card
        draw_card(gx, gy, 1.34, 1.9, CARD_BG, BORDER_BLUE)
        
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(gx + 0.47), Inches(gy + 0.1), Inches(0.4), Inches(0.4))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(gx + 0.52), Inches(gy + 0.15), Inches(0.3), Inches(0.3))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(gx + 0.05), Inches(gy + 0.55), Inches(1.24), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        
        r1 = p.add_run()
        r1.text = title + "\n\n"
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = CYAN
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(6.8)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    # --- RIGHT COLUMN: Adaptability Framework ---
    draw_card(6.6, 0.95, 6.3, 4.6, CARD_BG, BORDER_BLUE)
    draw_card(6.6, 0.95, 6.3, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(6.7, 1.0, 6.1, 0.25, [{"text": "ADAPTABILITY FRAMEWORK", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Stages flow inside framework card
    stages = [
        ("DEDICATED SECURE\nAIRBUS ODC", "icon_shield_w.png", 6.75, 1.5, 1.8, 1.2),
        ("BUSINESS CHANGE", "icon_gear_w.png", 8.8, 1.5, 1.2, 0.7),
        ("SCALABLE\nTALENT POOL", "icon_group_w.png", 10.3, 1.5, 1.2, 0.7),
        ("SAFe / Agile\nWaterfall", "icon_process_w.png", 8.8, 2.5, 2.7, 0.8),
        ("DEVSECOPS &\nAUTOMATION", "icon_rocket_w.png", 8.8, 3.65, 1.7, 0.8),
        ("CONTINUOUS\nIMPROVEMENT", "icon_excellence.png", 10.8, 3.65, 1.7, 0.8)
    ]
    for s_title, icon_file, sx, sy, sw, sh_h in stages:
        draw_card(sx, sy, sw, sh_h, CARD_BG, BORDER_BLUE)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(sx + 0.1), Inches(sy + 0.05), Inches(0.24), Inches(0.24))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(sx + 0.05), Inches(sy + 0.32), Inches(sw - 0.1), Inches(sh_h - 0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run()
        r1.text = s_title
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"

    # Connectors
    draw_connector_line(8.6, 1.85, 0.15, 0.02, CYAN)
    draw_connector_line(10.1, 1.85, 0.15, 0.02, CYAN)
    draw_connector_line(10.6, 4.0, 0.15, 0.02, CYAN)

    # --- BOTTOM SECTION: KEY BUSINESS OUTCOMES BANNER ---
    banner_bg2 = draw_card(0.4, 5.75, 12.53, 0.9, CARD_BG, GOLD)
    
    # Left Header badge
    draw_card(0.4, 5.75, 1.5, 0.9, RGBColor(12, 35, 75), GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(1.0), Inches(5.82), Inches(0.28), Inches(0.28))
    except:
        pass
    add_text_box(0.4, 6.22, 1.5, 0.35, [{"text": "KEY BUSINESS\nOUTCOMES", "bold": True, "size": 7.5, "color": GOLD}], PP_ALIGN.CENTER)

    # 6 Columns inside
    outcomes = [
        ("FASTER TIME\nTO MARKET", "icon_calendar_w.png", 2.0),
        ("HIGHER QUALITY\n& RELIABILITY", "icon_excellence.png", 3.8),
        ("IMPROVED OPERATIONAL\nRESILIENCE", "icon_shield_w.png", 5.6),
        ("OPTIMIZED COST\n& EFFICIENCY", "icon_gear_w.png", 7.4),
        ("ENHANCED USER\nEXPERIENCE", "icon_group_w.png", 9.2),
        ("SUSTAINABLE DIGITAL\nTRANSFORMATION", "icon_rocket_w.png", 11.0)
    ]
    for idx, (o_title, icon_file, ox) in enumerate(outcomes):
        if idx > 0:
            draw_connector_line(ox, 5.8, 0.015, 0.8, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(ox + 0.15), Inches(5.85), Inches(0.26), Inches(0.26))
        except:
            pass
            
        add_text_box(ox + 0.45, 5.85, 1.3, 0.7, [{"text": o_title, "bold": True, "size": 7, "color": WHITE}])

    draw_connector_line(0.4, 6.8, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.88, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.88, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


def build_slide_13():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "AI-AUGMENTED AGILE DELIVERY LIFECYCLE\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "Faster Delivery  |  Better Quality  |  Continuous Improvement"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- 7 LIFECYCLE STEPS ---
    step_w = 1.6
    step_h = 2.1
    spacing = 0.2
    
    steps_data = [
        ("1. BUSINESS\nNEED", "icon_target_w.png", "icon_group_w.png", "Identify opportunity\n& define value"),
        ("2. AGILE\nPLANNING", "icon_calendar_w.png", "icon_group_w.png", "Prioritize backlog\n& plan sprints"),
        ("3. SPRINT\nEXECUTION", "icon_workflow_w.png", "icon_code_w.png", "Build, integrate\n& collaborate"),
        ("4. VALIDATION\n& TESTING", "icon_shield_w.png", "icon_gear_w.png", "Ensure quality\n& reliability"),
        ("5. RELEASE", "icon_rocket_w.png", "icon_cloud_w.png", "Deploy with confidence\n& governance"),
        ("6. HYPERCARE", "icon_chat_w.png", "icon_gear_w.png", "Monitor, support\n& stabilize"),
        ("7. CONTINUOUS\nIMPROVEMENT", "icon_excellence.png", "icon_workflow_w.png", "Learn, optimize\n& deliver more value")
    ]
    
    for idx, (title, icon1, icon2, desc) in enumerate(steps_data):
        x_pos = 0.4 + idx * (step_w + spacing)
        
        # Rounded Card
        draw_card(x_pos, 1.15, step_w, step_h, CARD_BG, BORDER_BLUE)
        
        # Top Circle Icon
        c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.55), Inches(1.22), Inches(0.5), Inches(0.5))
        c1.fill.solid()
        c1.fill.fore_color.rgb = RGBColor(12, 35, 75)
        c1.line.color.rgb = GOLD
        c1.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon1), Inches(x_pos + 0.65), Inches(1.32), Inches(0.3), Inches(0.3))
        except:
            pass
            
        # Title text box
        add_text_box(x_pos + 0.05, 1.77, step_w - 0.1, 0.4, [{"text": title, "bold": True, "size": 7.5, "color": CYAN}], PP_ALIGN.CENTER)
        
        # Middle Circle Icon
        c2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.65), Inches(2.22), Inches(0.3), Inches(0.3))
        c2.fill.solid()
        c2.fill.fore_color.rgb = RGBColor(12, 35, 75)
        c2.line.color.rgb = CYAN
        c2.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon2), Inches(x_pos + 0.7), Inches(2.27), Inches(0.2), Inches(0.2))
        except:
            pass
            
        # Desc text box
        add_text_box(x_pos + 0.05, 2.57, step_w - 0.1, 0.6, [{"text": desc, "size": 6.8, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Connecting Arrow (except last)
        if idx < 6:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x_pos + 1.63), Inches(1.95), Inches(0.14), Inches(0.18))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # --- MIDDLE SECTION: AI ASSISTED ACROSS LIFECYCLE ---
    draw_connector_line(0.4, 3.42, 12.5, 0.015, BORDER_BLUE)
    tb_ai = slide.shapes.add_textbox(Inches(5.0), Inches(3.32), Inches(3.3), Inches(0.25))
    p_ai = tb_ai.text_frame.paragraphs[0]
    p_ai.alignment = PP_ALIGN.CENTER
    r_ai = p_ai.add_run()
    r_ai.text = " AI ASSISTED ACROSS THE LIFECYCLE "
    r_ai.font.bold = True
    r_ai.font.size = Pt(8.5)
    r_ai.font.color.rgb = CYAN
    r_ai.font.name = "Arial"

    ai_steps = [
        ("AI Planning", "icon_excellence.png", 0.6),
        ("AI Coding", "icon_code_w.png", 3.1),
        ("AI Testing", "icon_gear_w.png", 5.6),
        ("AI Release Assistant", "icon_rocket_w.png", 8.1),
        ("AI Knowledge Assistant", "icon_diploma_w.png", 10.6)
    ]
    for idx, (title, sub_icon, x_pos) in enumerate(ai_steps):
        # Circle icon background
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.65), Inches(3.55), Inches(0.8), Inches(0.8))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.8)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, "icon_robot.png"), Inches(x_pos + 0.9), Inches(3.8), Inches(0.3), Inches(0.3))
        except:
            pass
            
        # Small Sub-icon on the right
        c_sub = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 1.25), Inches(3.62), Inches(0.3), Inches(0.3))
        c_sub.fill.solid()
        c_sub.fill.fore_color.rgb = RGBColor(12, 35, 75)
        c_sub.line.color.rgb = GOLD
        c_sub.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, sub_icon), Inches(x_pos + 1.3), Inches(3.67), Inches(0.2), Inches(0.2))
        except:
            pass

        # Text label
        add_text_box(x_pos, 4.42, 2.1, 0.3, [{"text": title, "bold": True, "size": 8, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Connectors
        if idx < 4:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x_pos + 1.85), Inches(3.85), Inches(0.3), Inches(0.15))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # --- BOTTOM SECTION: KEY STAKEHOLDERS & DELIVERY OUTCOMES ---
    # Left Card: Key Stakeholders
    draw_card(0.4, 4.82, 5.6, 0.9, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 4.82, 5.6, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 4.85, 5.4, 0.22, [{"text": "KEY STAKEHOLDERS", "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)

    stakeholders = [
        ("Product Owner", "icon_people.png", 0.5),
        ("Scrum Master", "icon_workflow_w.png", 1.4),
        ("Development Team", "icon_group_w.png", 2.3),
        ("QA / Test Team", "icon_shield_w.png", 3.2),
        ("DevOps Team", "icon_network_w.png", 4.1),
        ("Architecture & Security", "icon_excellence.png", 5.0)
    ]
    for name, icon_file, cx in stakeholders:
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(5.15), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.05), Inches(5.2), Inches(0.25), Inches(0.25))
        except:
            pass
        # Text label below
        add_text_box(cx - 0.2, 5.52, 0.75, 0.25, [{"text": name, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Right Card: Delivery Outcomes
    draw_card(6.2, 4.82, 6.7, 0.9, CARD_BG, BORDER_BLUE)
    draw_card(6.2, 4.82, 6.7, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(6.3, 4.85, 6.5, 0.22, [{"text": "DELIVERY OUTCOMES", "bold": True, "size": 8, "color": CYAN}], PP_ALIGN.CENTER)

    outcomes = [
        ("Faster Time\nto Market", "icon_calendar_w.png", 6.3),
        ("Higher\nQuality", "icon_badge_w.png", 7.4),
        ("Predictable\nReleases", "icon_rocket_w.png", 8.5),
        ("Better User\nExperience", "icon_excellence.png", 9.6),
        ("Operational\nExcellence", "icon_gear_w.png", 10.7),
        ("Continuous\nImprovement", "icon_excellence.png", 11.8)
    ]
    for name, icon_file, cx in outcomes:
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.25), Inches(5.15), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = GOLD
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.3), Inches(5.2), Inches(0.25), Inches(0.25))
        except:
            pass
        # Text label below
        add_text_box(cx, 5.52, 0.85, 0.25, [{"text": name, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # --- 6. BOTTOM-MOST BANNER ---
    draw_card(0.4, 5.82, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("OUR ENABLERS", "icon_excellence.png"),
        ("Human Oversight", "icon_people.png"),
        ("Security By Design", "icon_shield_w.png"),
        ("Quality Gates", "icon_badge_w.png"),
        ("AI As An Accelerator", "icon_robot.png"),
        ("Continuous Learning", "icon_diploma_w.png")
    ]
    
    slot_w = 12.53 / 6.0
    for idx, (title, icon_file) in enumerate(footer_segments):
        x_pos = 0.4 + idx * slot_w
        
        # Draw separators
        if idx > 0:
            draw_connector_line(x_pos, 5.87, 0.015, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.12), Inches(5.92), Inches(0.28), Inches(0.28))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(x_pos + 0.45), Inches(5.88), Inches(slot_w - 0.5), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GOLD if idx == 0 else WHITE
        r1.font.name = "Arial"

    # Slide footer text at the very bottom
    draw_connector_line(0.4, 6.52, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.6, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.6, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 14 GENERATION
# ==========================================
def build_slide_14():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "AI-AUGMENTED WATERFALL DELIVERY LIFECYCLE\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "Governance-Driven  |  Quality by Design  |  Operationally Ready"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = GOLD

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- 7 WATERFALL PHASES ---
    step_w = 1.6
    step_h = 2.1
    spacing = 0.2
    
    steps_data = [
        ("1. REQUIREMENTS", "icon_target_w.png", "Requirements\nElicitation &\nBaseline"),
        ("2. SOLUTION\nDESIGN", "icon_process_w.png", "Solution Architecture\n& Detailed Design"),
        ("3. DEVELOPMENT\n& BUILD", "icon_code_w.png", "Development,\nCode Reviews &\nUnit Testing"),
        ("4. TESTING &\nVALIDATION", "icon_shield_w.png", "System, Integration,\nRegression,\nPerformance Testing"),
        ("5. DEPLOYMENT", "icon_rocket_w.png", "CAB Approval,\nDeployment Execution\n& Validation"),
        ("6. HYPERCARE /\nELS", "icon_chat_w.png", "Hypercare Support,\nMonitoring &\nDefect Fixes"),
        ("7. WP2 OPERATIONS\nHANDOVER", "icon_workflow_w.png", "Operational Handover,\nRunbook Transfer &\nStabilization")
    ]
    
    for idx, (title, icon_file, desc) in enumerate(steps_data):
        x_pos = 0.4 + idx * (step_w + spacing)
        
        # Rounded Card
        draw_card(x_pos, 1.15, step_w, step_h, CARD_BG, BORDER_BLUE)
        
        # Circle icon background
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.55), Inches(1.22), Inches(0.5), Inches(0.5))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.65), Inches(1.32), Inches(0.3), Inches(0.3))
        except:
            pass
            
        # Title text box
        add_text_box(x_pos + 0.05, 1.77, step_w - 0.1, 0.4, [{"text": title, "bold": True, "size": 7.5, "color": GOLD}], PP_ALIGN.CENTER)
        
        # Desc text box
        add_text_box(x_pos + 0.05, 2.37, step_w - 0.1, 0.8, [{"text": desc, "size": 6.8, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Connecting Arrow (except last)
        if idx < 6:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x_pos + 1.63), Inches(1.95), Inches(0.14), Inches(0.18))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # --- MIDDLE SECTION: AI-AUGMENTATION ACROSS LIFECYCLE ---
    draw_connector_line(0.4, 3.42, 7.8, 0.015, BORDER_BLUE)
    tb_ai = slide.shapes.add_textbox(Inches(2.0), Inches(3.32), Inches(4.6), Inches(0.25))
    p_ai = tb_ai.text_frame.paragraphs[0]
    p_ai.alignment = PP_ALIGN.CENTER
    r_ai = p_ai.add_run()
    r_ai.text = " AI-AUGMENTATION ACROSS THE LIFECYCLE "
    r_ai.font.bold = True
    r_ai.font.size = Pt(8)
    r_ai.font.color.rgb = CYAN
    r_ai.font.name = "Arial"

    ai_steps = [
        ("AI Requirements\nAnalysis", 0.5),
        ("AI Design\nAssistant", 1.55),
        ("AI Code\nAssistant", 2.60),
        ("AI Test\nGeneration", 3.65),
        ("AI Defect\nAnalytics", 4.70),
        ("AI\nDocumentation", 5.75),
        ("AI Knowledge\nAssistant", 6.80)
    ]
    for idx, (title, x_pos) in enumerate(ai_steps):
        # Circle icon background
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.25), Inches(3.55), Inches(0.4), Inches(0.4))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, "icon_robot.png"), Inches(x_pos + 0.32), Inches(3.62), Inches(0.25), Inches(0.25))
        except:
            pass

        # Text label
        add_text_box(x_pos, 4.05, 0.9, 0.35, [{"text": title, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Connectors
        if idx < 6:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x_pos + 0.72), Inches(3.65), Inches(0.15), Inches(0.1))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # --- GOVERNANCE GATES ---
    draw_connector_line(0.4, 4.52, 7.8, 0.015, BORDER_BLUE)
    tb_gov = slide.shapes.add_textbox(Inches(2.5), Inches(4.42), Inches(3.6), Inches(0.25))
    p_gov = tb_gov.text_frame.paragraphs[0]
    p_gov.alignment = PP_ALIGN.CENTER
    r_gov = p_gov.add_run()
    r_gov.text = " GOVERNANCE GATES "
    r_gov.font.bold = True
    r_gov.font.size = Pt(8)
    r_gov.font.color.rgb = CYAN
    r_gov.font.name = "Arial"

    gates = [
        ("G1", "Requirements\nApproved", 0.5),
        ("G2", "Design\nApproved", 1.55),
        ("G3", "Build\nComplete", 2.60),
        ("G4", "Testing\nPassed", 3.65),
        ("G5", "Production\nReady", 4.70),
        ("G6", "Go Live\nApproved", 5.75),
        ("G7", "Hypercare\nExit Approved", 6.80)
    ]
    for idx, (label, desc, x_pos) in enumerate(gates):
        # Circle background
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x_pos + 0.22), Inches(4.75), Inches(0.45), Inches(0.45))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = GOLD
        circ.line.width = Pt(0.7)
        add_text_box(x_pos + 0.22, 4.8, 0.45, 0.35, [{"text": label, "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)
        
        # Text label
        add_text_box(x_pos, 5.25, 0.9, 0.35, [{"text": desc, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)

    # --- TOOLCHAIN & INTEGRATION ---
    draw_connector_line(0.4, 5.62, 7.8, 0.015, BORDER_BLUE)
    tb_tools = slide.shapes.add_textbox(Inches(2.5), Inches(5.52), Inches(3.6), Inches(0.25))
    p_tools = tb_tools.text_frame.paragraphs[0]
    p_tools.alignment = PP_ALIGN.CENTER
    r_tools = p_tools.add_run()
    r_tools.text = " TOOLCHAIN & INTEGRATION "
    r_tools.font.bold = True
    r_tools.font.size = Pt(8)
    r_tools.font.color.rgb = CYAN
    r_tools.font.name = "Arial"

    tool_logos = [
        ("logo_jira_c.png", 0.5, 0.8),
        ("logo_confluence_c.png", 1.6, 0.95),
        ("logo_gitlab_c.png", 2.8, 0.8),
        ("logo_dynatrace_c.png", 4.0, 0.9),
        ("logo_servicenow_c.png", 5.2, 0.9)
    ]
    for logo_file, x_pos, w_size in tool_logos:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, logo_file), Inches(x_pos), Inches(5.82), Inches(w_size), Inches(0.3))
        except:
            pass

    # --- RIGHT COLUMN: Outcomes & Dedicated ODC ---
    # Card 1: Key Outcomes
    draw_card(8.4, 3.35, 4.5, 2.1, CARD_BG, BORDER_BLUE)
    draw_card(8.4, 3.35, 4.5, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.5, 3.38, 4.3, 0.22, [{"text": "KEY OUTCOMES", "bold": True, "size": 8, "color": CYAN}], PP_ALIGN.CENTER)

    outcomes = [
        ("Predictable\nDelivery", "icon_excellence.png", 8.45),
        ("End-to-End\nTraceability", "icon_diploma_w.png", 9.15),
        ("Security &\nCompliance", "icon_shield_w.png", 9.85),
        ("Deployment\nReliability", "icon_rocket_w.png", 10.55),
        ("Operational\nReadiness", "icon_gear_w.png", 11.25),
        ("Seamless WP2\nHandover", "icon_workflow_w.png", 11.95)
    ]
    for idx, (name, icon_file, cx) in enumerate(outcomes):
        # Icon Circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.12), Inches(3.68), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = GOLD
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.17), Inches(3.73), Inches(0.25), Inches(0.25))
        except:
            pass
        # Text label below
        add_text_box(cx, 4.08, 0.6, 0.35, [{"text": name, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)

    # Card 2: Dedicated ODC
    draw_card(8.4, 5.52, 4.5, 0.9, CARD_BG, BORDER_BLUE)
    c_odc = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.55), Inches(5.6), Inches(0.4), Inches(0.4))
    c_odc.fill.solid()
    c_odc.fill.fore_color.rgb = RGBColor(12, 35, 75)
    c_odc.line.color.rgb = CYAN
    c_odc.line.width = Pt(0.7)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_shield_w.png"), Inches(8.6), Inches(5.65), Inches(0.3), Inches(0.3))
    except:
        pass
        
    add_text_box(9.1, 5.55, 3.7, 0.3, [{"text": "DEDICATED SECURE AIRBUS ODC", "bold": True, "size": 7.5, "color": CYAN}])
    
    bullets = "• Segregated Environment  • RBAC & Access Control\n• Export Control Awareness  • GDPR & Data Protection\n• Business Continuity & Disaster Recovery"
    add_text_box(9.1, 5.8, 3.7, 0.55, [{"text": bullets, "size": 6.5, "color": TEXT_MUTED}])

    # --- 6. BOTTOM-MOST BANNER ---
    draw_card(0.4, 6.45, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("OUR ENABLERS", "icon_excellence.png"),
        ("Quality", "icon_badge_w.png"),
        ("Security", "icon_shield_w.png"),
        ("Delivery", "icon_rocket_w.png"),
        ("Excellence", "icon_excellence.png")
    ]
    
    slot_w = 12.53 / 5.0
    for idx, (title, icon_file) in enumerate(footer_segments):
        x_pos = 0.4 + idx * slot_w
        
        # Draw separators
        if idx > 0:
            draw_connector_line(x_pos, 6.5, 0.015, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(x_pos + 0.12), Inches(6.55), Inches(0.28), Inches(0.28))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(x_pos + 0.45), Inches(6.51), Inches(slot_w - 0.5), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GOLD if idx == 0 else WHITE
        r1.font.name = "Arial"

    draw_connector_line(0.4, 6.95, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 7.02, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 7.02, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 16 GENERATION
# ==========================================
def build_slide_16():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "Integrated Target Operating Model\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = WHITE
    
    r_t2 = p_title.add_run()
    r_t2.text = "Airbus Digital Operations - Build, Run & Govern"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- LEFT SECTION: TARGET OPERATING MODEL LAYERS ---
    row_y = [0.95, 1.53, 2.11, 2.69, 3.27, 3.85]
    row_headers = [
        ("Top Layer\nGovernance &\nStrategic Control", "icon_excellence.png", [
            ("Steering\nCommittee", "icon_group_w.png"),
            ("Service\nReview Board", "icon_calendar_w.png"),
            ("Architecture\nGovernance", "icon_excellence.png"),
            ("Vendor\nManagement", "icon_workflow_w.png")
        ], 4),
        
        ("Observability &\nMonitoring", "icon_gear_w.png", [
            ("Zabbix", "icon_network_w.png"),
            ("Grafana", "icon_excellence.png"),
            ("Splunk", "icon_excellence.png"),
            ("Application\nMonitoring", "icon_gear_w.png"),
            ("AI-Powered\nObservability", "icon_robot.png")
        ], 5),
        
        ("WP2\nRun Operations", "icon_gear_w.png", [
            ("Incident\nManagement", "icon_chat_w.png"),
            ("Change\nManagement", "icon_workflow_w.png"),
            ("Problem\nManagement", "icon_shield_w.png"),
            ("Platform\nOperations", "icon_excellence.png"),
            ("Mainframe\nSupport", "icon_company_w.png"),
            ("AI Service Desk\nCopilot", "icon_robot.png")
        ], 6),
        
        ("WP1\nBuild Services", "icon_code_w.png", [
            ("Agile\nDelivery", "icon_rocket_w.png"),
            ("DevSecOps", "icon_workflow_w.png"),
            ("Quality\nEngineering", "icon_badge_w.png"),
            ("Solution\nEngineering", "icon_excellence.png"),
            ("Test\nAutomation", "icon_gear_w.png")
        ], 5),
        
        ("WP3\nGovernance\nServices", "icon_excellence.png", [
            ("Release\nManagement", "icon_rocket_w.png"),
            ("PMO\nServices", "icon_group_w.png"),
            ("Business\nAnalysis", "icon_excellence.png"),
            ("End-to-End\nTesting", "icon_shield_w.png"),
            ("Scrum\nServices", "icon_workflow_w.png"),
            ("Technical Delivery\nServices", "icon_excellence.png")
        ], 6),
        
        ("Shared\nServices", "icon_group_w.png", [
            ("Security &\nCompliance", "icon_shield_w.png"),
            ("Knowledge\nManagement", "icon_diploma_w.png"),
            ("Automation\nFactory", "icon_gear_w.png"),
            ("Reporting &\nAnalytics", "icon_excellence.png"),
            ("CSI\nGovernance", "icon_excellence.png")
        ], 5)
    ]

    for idx, (header_text, header_icon, items, item_count) in enumerate(row_headers):
        ry = row_y[idx]
        
        # Left label block
        draw_card(0.4, ry, 1.8, 0.5, RGBColor(12, 35, 75), BORDER_BLUE)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, header_icon), Inches(0.48), Inches(ry + 0.1), Inches(0.3), Inches(0.3))
        except:
            pass
        add_text_box(0.85, ry + 0.05, 1.3, 0.4, [{"text": header_text, "bold": True, "size": 6.8, "color": WHITE}])

        # Right content card
        draw_card(2.3, ry, 7.7, 0.5, CARD_BG, BORDER_BLUE)
        
        # Draw items horizontally inside content card
        col_w = 7.5 / item_count
        for c_idx, (item_name, item_icon) in enumerate(items):
            ix = 2.4 + c_idx * col_w
            # Draw separator line in between (except first)
            if c_idx > 0:
                draw_connector_line(ix - 0.05, ry + 0.08, 0.015, 0.34, BORDER_BLUE)
                
            try:
                slide.shapes.add_picture(os.path.join(icons_dir, item_icon), Inches(ix), Inches(ry + 0.12), Inches(0.24), Inches(0.24))
            except:
                pass
                
            add_text_box(ix + 0.28, ry + 0.08, col_w - 0.35, 0.34, [{"text": item_name, "bold": True, "size": 6.5, "color": WHITE}])

    # Row 7: Customer Experience Portal (ServiceNow)
    ry7 = 4.43
    draw_card(0.4, ry7, 1.8, 1.0, RGBColor(12, 35, 75), BORDER_BLUE)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(0.48), Inches(ry7 + 0.35), Inches(0.3), Inches(0.3))
    except:
        pass
    add_text_box(0.85, ry7 + 0.25, 1.3, 0.5, [{"text": "Customer\nExperience\nPortal", "bold": True, "size": 7.5, "color": WHITE}])

    draw_card(2.3, ry7, 7.7, 1.0, CARD_BG, BORDER_BLUE)
    
    # ServiceNow branding
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_servicenow_c.png"), Inches(2.4), Inches(ry7 + 0.25), Inches(1.3), Inches(0.3))
    except:
        pass
    add_text_box(2.4, ry7 + 0.58, 1.3, 0.25, [{"text": "P O R T A L", "bold": True, "size": 7.5, "color": CYAN}])

    # 5 ServiceNow circle modules
    now_modules = [
        ("Incidents", "icon_chat_w.png", 3.85),
        ("Requests", "icon_excellence.png", 4.65),
        ("Problems", "icon_shield_w.png", 5.45),
        ("Changes", "icon_workflow_w.png", 6.25),
        ("Knowledge\nBase", "icon_diploma_w.png", 7.05)
    ]
    for name, icon_file, mx in now_modules:
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(mx + 0.15), Inches(ry7 + 0.15), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(mx + 0.2), Inches(ry7 + 0.2), Inches(0.25), Inches(0.25))
        except:
            pass
        add_text_box(mx, ry7 + 0.55, 0.65, 0.35, [{"text": name, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Laptop image
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide16_laptop.png"), Inches(8.05), Inches(ry7 + 0.05), Inches(1.85), Inches(0.9))
    except:
        pass

    # --- RIGHT COLUMN: Why Akkodis ---
    draw_card(10.15, 0.95, 2.78, 4.48, CARD_BG, BORDER_BLUE)
    draw_card(10.15, 0.95, 2.78, 0.35, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(10.25, 1.0, 2.58, 0.25, [{"text": "Why Akkodis", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)

    reasons = [
        ("Airbus Domain Expertise", "icon_globe_w.png"),
        ("Operational Excellence", "icon_gear_w.png"),
        ("AI-Enabled Service Delivery", "icon_robot.png"),
        ("Dedicated Secure Airbus ODC", "icon_shield_w.png"),
        ("Build + Run + Govern Model", "icon_workflow_w.png"),
        ("Industrial Digitalization", "icon_company_w.png"),
        ("SCADA, Kafka & Aerostructures", "icon_network_w.png"),
        ("AR/VR & Connected Worker", "icon_arvr_headset.png")
    ]
    for idx, (reason_title, icon_file) in enumerate(reasons):
        y_pos = 1.35 + idx * 0.36
        # Green checkmark badge
        chk = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.25), Inches(y_pos + 0.02), Inches(0.16), Inches(0.16))
        chk.fill.solid()
        chk.fill.fore_color.rgb = GREEN_BORDER
        chk.line.fill.background()
        add_text_box(10.25, y_pos, 0.16, 0.16, [{"text": "✔", "bold": True, "size": 5.5, "color": WHITE}], PP_ALIGN.CENTER)
        
        # Reason title
        add_text_box(10.46, y_pos - 0.02, 2.1, 0.32, [{"text": reason_title, "bold": True, "size": 6.8, "color": WHITE}])
        
        # Small monographic icon on the right
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(12.6), Inches(y_pos + 0.02), Inches(0.18), Inches(0.18))
        except:
            pass

    # VR Worker image
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide16_vr_worker.png"), Inches(10.2), Inches(4.38), Inches(2.68), Inches(1.0))
    except:
        pass

    # --- BOTTOM SECTION: BUSINESS OUTCOMES BANNER ---
    draw_card(0.4, 5.52, 12.53, 1.0, CARD_BG, GOLD)
    
    # Left Header badge
    draw_card(0.4, 5.52, 1.8, 1.0, RGBColor(12, 35, 75), GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(1.15), Inches(5.58), Inches(0.3), Inches(0.3))
    except:
        pass
    add_text_box(0.4, 6.02, 1.8, 0.35, [{"text": "Business Outcomes", "bold": True, "size": 8.5, "color": GOLD}], PP_ALIGN.CENTER)

    # 8 Outcomes columns
    outcomes_data = [
        ("Faster Time\nto Market", "icon_rocket_w.png", 2.3),
        ("Higher SLA\nCompliance", "icon_excellence.png", 3.6),
        ("Improved\nSecurity", "icon_shield_w.png", 4.9),
        ("Reduced\nMTTR", "icon_gear_w.png", 6.2),
        ("Increased\nAutomation", "icon_robot.png", 7.5),
        ("Lower\nOperational Cost", "icon_excellence.png", 8.8),
        ("Better User\nExperience", "icon_group_w.png", 10.1),
        ("Continuous\nImprovement", "icon_excellence.png", 11.4)
    ]
    for idx, (o_title, icon_file, ox) in enumerate(outcomes_data):
        if idx > 0:
            draw_connector_line(ox, 5.58, 0.015, 0.88, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(ox + 0.45), Inches(5.62), Inches(0.28), Inches(0.28))
        except:
            pass
            
        add_text_box(ox, 5.98, 1.25, 0.48, [{"text": o_title, "bold": True, "size": 6.8, "color": WHITE}], PP_ALIGN.CENTER)

    draw_connector_line(0.4, 6.62, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.7, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.7, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 17 GENERATION
# ==========================================
def build_slide_17():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    r_t1 = p_title.add_run()
    r_t1.text = "WP3 "
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "- DELIVERY GOVERNANCE & TRANSFORMATION SERVICES\n"
    r_t2.font.name = "Times New Roman"
    r_t2.font.size = Pt(28)
    r_t2.font.bold = True
    r_t2.font.color.rgb = WHITE
    
    r_t3 = p_title.add_run()
    r_t3.text = "Agile Delivery | PMO Governance | DevSecOps & CI/CD | Quality Engineering | Knowledge Transfer"
    r_t3.font.name = "Arial"
    r_t3.font.size = Pt(11)
    r_t3.font.bold = True
    r_t3.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- TOP ROW: Project Services Lead & CoE Roles ---
    draw_card(0.4, 0.95, 10.5, 0.8, CARD_BG, BORDER_BLUE)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_people.png"), Inches(0.55), Inches(1.05), Inches(0.5), Inches(0.5))
    except:
        pass
        
    add_text_box(1.15, 1.0, 2.2, 0.7, [
        {"text": "WP3 PROJECT SERVICES LEAD\n", "bold": True, "size": 8, "color": GOLD},
        {"text": "• Agile Excellence  • PMO Governance\n• DevSecOps  • Quality Assurance", "size": 6.8, "color": WHITE}
    ])
    
    draw_connector_line(3.45, 1.0, 0.015, 0.7, BORDER_BLUE)
    
    add_text_box(3.55, 1.0, 3.2, 0.7, [
        {"text": "Key Focus Areas\n", "bold": True, "size": 8, "color": CYAN},
        {"text": "• Stakeholder Management\n• Delivery Oversight & Delivery Excellence", "size": 6.8, "color": WHITE}
    ])

    draw_connector_line(6.8, 1.0, 0.015, 0.7, BORDER_BLUE)

    # 4 Roles circles on the right
    roles = [
        ("Scrum\nMasters", "icon_group_w.png", 6.95),
        ("Project\nManagers", "icon_people.png", 7.85),
        ("DevOps\nLeads", "icon_workflow_w.png", 8.75),
        ("Quality\nLeads", "icon_shield_w.png", 9.65)
    ]
    for name, icon_file, cx in roles:
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.1), Inches(1.0), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(1.05), Inches(0.25), Inches(0.25))
        except:
            pass
        add_text_box(cx, 1.4, 0.55, 0.3, [{"text": name, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)

    # --- MIDDLE SECTION: Agile Delivery & PMO/DevOps/QA Excellence ---
    # Left Card: Agile Delivery Excellence
    draw_card(0.4, 1.83, 5.2, 2.1, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 1.83, 5.2, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 1.86, 5.0, 0.22, [{"text": "AGILE DELIVERY EXCELLENCE", "bold": True, "size": 8, "color": CYAN}], PP_ALIGN.CENTER)

    # Circular loop flow
    circ_loop = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.55), Inches(2.2), Inches(1.2), Inches(1.2))
    circ_loop.fill.solid()
    circ_loop.fill.fore_color.rgb = RGBColor(12, 35, 75)
    circ_loop.line.color.rgb = CYAN
    circ_loop.line.width = Pt(0.8)
    add_text_box(0.55, 2.6, 1.2, 0.4, [
        {"text": "AGILE\nLIFECYCLE", "bold": True, "size": 7, "color": GOLD}
    ], PP_ALIGN.CENTER)

    # Loop labels
    add_text_box(0.55, 2.12, 1.2, 0.2, [{"text": "PLAN", "bold": True, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)
    add_text_box(0.55, 3.25, 1.2, 0.2, [{"text": "TEST", "bold": True, "size": 6.5, "color": WHITE}], PP_ALIGN.CENTER)
    add_text_box(1.5, 2.7, 0.5, 0.2, [{"text": "BUILD", "bold": True, "size": 6.5, "color": WHITE}])
    add_text_box(0.1, 2.7, 0.55, 0.2, [{"text": "REVIEW", "bold": True, "size": 6.5, "color": WHITE}], PP_ALIGN.RIGHT)

    # Teams structure
    add_text_box(1.9, 2.2, 1.6, 1.6, [
        {"text": "Scrum Master 1\n", "bold": True, "size": 7.5, "color": GOLD},
        {"text": "Teams 1-3  (25+ resources)\n\n", "size": 7, "color": WHITE},
        {"text": "Scrum Master 2\n", "bold": True, "size": 7.5, "color": GOLD},
        {"text": "Teams 4-6  (25+ resources)\n\n", "size": 7, "color": WHITE},
        {"text": "Scrum Master 3\n", "bold": True, "size": 7.5, "color": GOLD},
        {"text": "Teams 7-9  (25+ resources)", "size": 7, "color": WHITE}
    ])

    # Checkmarks list
    add_text_box(3.6, 2.2, 1.9, 1.6, [
        {"text": "✔ Sprint Planning\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Daily Stand-ups\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Sprint Reviews\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Retrospectives\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Team Coaching\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Velocity Management\n", "bold": True, "size": 7.5, "color": GREEN_BORDER},
        {"text": "✔ Backlog Grooming", "bold": True, "size": 7.5, "color": GREEN_BORDER}
    ])

    # Right Card: PMO / DEVOPS / QA EXCELLENCE
    draw_card(5.7, 1.83, 5.2, 2.1, CARD_BG, BORDER_BLUE)
    draw_card(5.7, 1.83, 5.2, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(5.8, 1.86, 5.0, 0.22, [{"text": "PMO / DEVOPS / QA EXCELLENCE", "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)

    # 4 columns inside
    pm_cols = [
        ("Portfolio\nManager", "icon_excellence.png", [
            "Portfolio\nGovernance", "Stakeholder\nManagement", "Budget\nOversight"
        ], 5.8, RGBColor(12, 35, 75), GOLD),
        
        ("Delivery\nManager", "icon_group_w.png", [
            "Program\nReporting", "Resource\nPlanning", "KPI Tracking"
        ], 7.05, CARD_BG, CYAN),
        
        ("DevSecOps\nLead", "icon_workflow_w.png", [
            "CI/CD\nAutomation", "Infrastructure\nas Code", "Release\nAutomation"
        ], 8.3, CARD_BG, WHITE),
        
        ("Quality\nEngineering Lead", "icon_shield_w.png", [
            "Test\nAutomation", "Quality\nGates", "Defect\nPrevention"
        ], 9.55, CARD_BG, WHITE)
    ]
    for p_title, p_icon, bullets, px, bg_col, border_col in pm_cols:
        draw_card(px, 2.2, 1.2, 1.6, bg_col, border_col)
        # Header text
        add_text_box(px, 2.22, 1.2, 0.35, [{"text": p_title, "bold": True, "size": 7, "color": border_col}], PP_ALIGN.CENTER)
        # Bullet list text
        bullets_text = ""
        for b in bullets:
            bullets_text += "• " + b + "\n"
        bullets_text = bullets_text.strip("\n")
        add_text_box(px + 0.05, 2.62, 1.1, 1.1, [{"text": bullets_text, "size": 6.5, "color": WHITE}])

    # --- RIGHT COLUMN: Dashboard & AI Copilot ---
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide17_dashboard.png"), Inches(11.0), Inches(0.95), Inches(1.9), Inches(1.9))
        slide.shapes.add_picture(os.path.join(icons_dir, "slide17_ai_copilot.png"), Inches(11.0), Inches(2.95), Inches(1.9), Inches(0.95))
    except:
        pass

    # --- Bottom-Left Cloud Security ---
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide17_cloud_security.png"), Inches(0.4), Inches(4.0), Inches(1.3), Inches(0.72))
    except:
        pass

    # --- Delivery Principles ---
    draw_card(1.8, 4.0, 9.1, 0.72, CARD_BG, BORDER_BLUE)
    draw_card(1.8, 4.0, 9.1, 0.22, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(1.9, 4.02, 8.9, 0.18, [{"text": "DELIVERY PRINCIPLES", "bold": True, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)

    principles = [
        ("Agile\nExcellence", "icon_excellence.png", 1.9),
        ("Transparency &\nCollaboration", "icon_group_w.png", 3.7),
        ("Quality & Security\nby Design", "icon_shield_w.png", 5.5),
        ("DevSecOps\nAutomation", "icon_workflow_w.png", 7.3),
        ("Data-Driven\nDecision Making", "icon_excellence.png", 9.1)
    ]
    for idx, (title, icon_file, cx) in enumerate(principles):
        if idx > 0:
            draw_connector_line(cx - 0.05, 4.28, 0.015, 0.4, BORDER_BLUE)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.1), Inches(4.32), Inches(0.24), Inches(0.24))
        except:
            pass
        add_text_box(cx + 0.38, 4.28, 1.35, 0.4, [{"text": title, "bold": True, "size": 6.8, "color": WHITE}])

    # --- GOVERNANCE CADENCE ---
    draw_card(0.4, 4.82, 12.53, 0.98, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 4.82, 12.53, 0.24, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 4.84, 12.33, 0.2, [{"text": "GOVERNANCE CADENCE", "bold": True, "size": 8, "color": GOLD}], PP_ALIGN.CENTER)

    cadences = [
        ("DAILY", "• Daily Stand-up\n• Sprint Progress\n• Blocker Resolution", "icon_calendar_w.png", 0.5),
        ("WEEKLY", "• Sprint Review\n• Retrospective\n• Velocity Tracking", "icon_excellence.png", 3.6),
        ("BI-WEEKLY", "• Sprint Planning\n• Backlog Grooming\n• Release Planning", "icon_workflow_w.png", 6.7),
        ("MONTHLY", "• Portfolio Review\n• RAID Dashboard\n• Budget Forecast", "icon_gear_w.png", 9.8)
    ]
    for idx, (c_title, c_bullets, icon_file, cx) in enumerate(cadences):
        if idx > 0:
            draw_connector_line(cx - 0.05, 5.12, 0.015, 0.62, BORDER_BLUE)
            
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.1), Inches(5.12), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(5.17), Inches(0.25), Inches(0.25))
        except:
            pass
            
        add_text_box(cx + 0.55, 5.12, 2.4, 0.62, [
            {"text": c_title + "\n", "bold": True, "size": 7.5, "color": GOLD},
            {"text": c_bullets, "size": 6.8, "color": WHITE}
        ])

    # --- BOTTOM-MOST BANNER ---
    draw_card(0.4, 5.92, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("90%+", "Sprint Success", "icon_excellence.png", 0.4),
        ("100%", "Deployment Success", "icon_rocket_w.png", 2.48),
        ("80%+", "Test Automation", "icon_badge_w.png", 4.56),
        ("95%+", "On-Time Delivery", "icon_excellence.png", 6.64),
        ("Zero", "Failed Releases", "icon_shield_w.png", 8.72),
        ("Seamless", "WP1 & WP2 Integration", "icon_workflow_w.png", 10.8)
    ]
    slot_w = 12.53 / 6.0
    for idx, (val, label, icon_file, cx) in enumerate(footer_segments):
        if idx > 0:
            draw_connector_line(cx, 5.97, 0.015, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.12), Inches(6.02), Inches(0.28), Inches(0.28))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(cx + 0.45), Inches(5.98), Inches(slot_w - 0.5), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = val + "  "
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"
        
        r2 = p.add_run()
        r2.text = label
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = WHITE
        r2.font.name = "Arial"

    draw_connector_line(0.4, 6.52, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.7, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.6, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 18 GENERATION
# ==========================================
def build_slide_18():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "OPERATIONAL EXCELLENCE PILLARS & PROCESS\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "Delivering Stable, Secure and High-Performing Digital Services that Power Airbus Operations"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- DEFINITION BANNER ---
    draw_card(0.4, 0.95, 12.53, 0.68, CARD_BG, BORDER_BLUE)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(0.55), Inches(1.08), Inches(0.4), Inches(0.4))
    except:
        pass
        
    add_text_box(1.05, 1.0, 5.8, 0.6, [
        {"text": "DEFINITION: ", "bold": True, "size": 8.5, "color": GOLD},
        {"text": "Delivering stable, secure, highly available, and continuously improving digital services that support Airbus manufacturing, quality, procurement, and operational environments while ensuring SLA compliance and business continuity.", "size": 7.5, "color": WHITE}
    ])
    
    draw_connector_line(6.9, 1.0, 0.015, 0.58, BORDER_BLUE)

    # Right side 4 modules
    def_mods = [
        ("Business\nAligned", "icon_group_w.png", 7.05),
        ("Secure by\nDesign", "icon_shield_w.png", 8.4),
        ("Data-Driven\nDecisions", "icon_excellence.png", 9.75),
        ("Continuous\nImprovement", "icon_workflow_w.png", 11.1)
    ]
    for name, icon_file, cx in def_mods:
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.1), Inches(1.12), Inches(0.26), Inches(0.26))
        except:
            pass
        add_text_box(cx + 0.42, 1.12, 0.95, 0.4, [{"text": name, "bold": True, "size": 7, "color": WHITE}])

    # --- LEFT COLUMN: Pillars ---
    draw_card(0.4, 1.75, 8.3, 4.6, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 1.75, 8.3, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 1.78, 8.1, 0.24, [{"text": "OUR OPERATIONAL EXCELLENCE PILLARS", "bold": True, "size": 9, "color": WHITE}], PP_ALIGN.CENTER)

    pillars_data = [
        ("1. PROACTIVE\nMONITORING &\nOBSERVABILITY", "icon_excellence.png", [
            "End-to-end monitoring", "Infrastructure checks", "Real-time dashboards", "Predictive alerting", "Event correlation"
        ], "Faster issue detection\n& reduced downtime", RGBColor(10, 50, 80), 0.5),
        
        ("2. INCIDENT &\nPROBLEM\nMANAGEMENT", "icon_chat_w.png", [
            "ITIL-aligned support", "Major Incident Mgmt", "Root Cause Analysis", "Escalation paths", "Knowledge reuse"
        ], "Reduced MTTR &\nimproved service\nreliability", RGBColor(15, 60, 70), 1.81),
        
        ("3. CHANGE &\nRELEASE\nEXCELLENCE", "icon_workflow_w.png", [
            "Controlled releases", "Automated validation", "CAB compliance", "Rollback readiness", "Hypercare support"
        ], "Higher release\nsuccess rate & lower\nproduction risk", RGBColor(15, 60, 30), 3.12),
        
        ("4. AUTOMATION &\nDEVSECOPS", "icon_rocket_w.png", [
            "CI/CD pipelines", "Infrastructure as Code", "Automated testing", "Security-by-design", "Process automation"
        ], "Faster delivery with\nimproved quality &\nsecurity", RGBColor(50, 20, 70), 4.43),
        
        ("5. KNOWLEDGE-\nCENTERED\nSUPPORT", "icon_diploma_w.png", [
            "Shift-left approach", "LLM-ready database", "Runbooks & wikis", "Cross-skilling", "Continuous learning"
        ], "Improved first-time\nresolution rate", RGBColor(80, 50, 10), 5.74),
        
        ("6. KPI-DRIVEN\nGOVERNANCE", "icon_excellence.png", [
            "SLA compliance", "Availability metrics", "MTTR tracking", "Change success rate", "CSI reviews"
        ], "Data-driven operational\nmanagement", RGBColor(10, 30, 60), 7.05)
    ]
    for title, icon_file, bullets, impact, impact_bg, px in pillars_data:
        # Card column
        draw_card(px, 2.15, 1.26, 4.1, CARD_BG, BORDER_BLUE)
        
        # Circle icon
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(px + 0.43), Inches(2.25), Inches(0.4), Inches(0.4))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(px + 0.5), Inches(2.32), Inches(0.26), Inches(0.26))
        except:
            pass
            
        # Title text box
        add_text_box(px, 2.7, 1.26, 0.6, [{"text": title, "bold": True, "size": 6.8, "color": GOLD}], PP_ALIGN.CENTER)
        
        # Bullet list text
        bullets_text = ""
        for b in bullets:
            bullets_text += "• " + b + "\n"
        bullets_text = bullets_text.strip("\n")
        add_text_box(px + 0.05, 3.35, 1.16, 1.8, [{"text": bullets_text, "size": 6, "color": WHITE}])

        # Bottom Impact Block
        draw_card(px, 5.5, 1.26, 0.75, impact_bg, None)
        add_text_box(px + 0.05, 5.55, 1.16, 0.65, [
            {"text": "IMPACT\n", "bold": True, "size": 6.5, "color": GOLD},
            {"text": impact, "size": 5.8, "color": WHITE}
        ], PP_ALIGN.CENTER)

    # --- RIGHT COLUMN: Process Model ---
    draw_card(8.8, 1.75, 4.13, 4.6, CARD_BG, BORDER_BLUE)
    draw_card(8.8, 1.75, 4.13, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.9, 1.78, 3.93, 0.24, [{"text": "OPERATIONAL EXCELLENCE PROCESS MODEL", "bold": True, "size": 8.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Native circular layout
    # Center circle
    circ_center = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.36), Inches(3.55), Inches(1.0), Inches(1.0))
    circ_center.fill.solid()
    circ_center.fill.fore_color.rgb = RGBColor(12, 35, 75)
    circ_center.line.color.rgb = CYAN
    circ_center.line.width = Pt(1)
    add_text_box(10.36, 3.8, 1.0, 0.5, [
        {"text": "CONTINUOUS\nIMPROVEMENT\n", "bold": True, "size": 7, "color": GOLD},
        {"text": "Better Every Day", "size": 5.8, "color": WHITE}
    ], PP_ALIGN.CENTER)

    # 5 Step Cards around center
    steps = [
        ("MONITOR", "icon_excellence.png", 10.36, 2.5, "Comprehensive monitoring\nacross stack"),
        ("DETECT", "icon_excellence.png", 11.6, 3.25, "Early detection with\nintelligent alerting"),
        ("RESOLVE", "icon_excellence.png", 11.2, 4.45, "Rapid resolution through\nautomation & expertise"),
        ("IMPROVE", "icon_excellence.png", 9.5, 4.45, "Root cause analysis &\nservice improvement"),
        ("AUTOMATE", "icon_robot.png", 9.1, 3.25, "AI-driven automated\noperations")
    ]
    for idx, (s_title, icon_file, sx, sy, s_desc) in enumerate(steps):
        # Small Step Card
        draw_card(sx, sy, 1.0, 0.75, CARD_BG, BORDER_BLUE)
        # Small icon
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(sx + 0.1), Inches(sy + 0.05), Inches(0.18), Inches(0.18))
        except:
            pass
        add_text_box(sx + 0.32, sy + 0.05, 0.65, 0.2, [{"text": s_title, "bold": True, "size": 6.8, "color": CYAN}])
        add_text_box(sx + 0.05, sy + 0.28, 0.9, 0.45, [{"text": s_desc, "size": 5.8, "color": TEXT_MUTED}])

    # Curved connecting arrows
    # We can draw nice straight connector lines to simulate the flow
    draw_connector_line(11.0, 3.3, 0.5, 0.02, CYAN) # Monitor -> Detect
    draw_connector_line(12.0, 4.1, 0.02, 0.3, CYAN) # Detect -> Resolve
    draw_connector_line(10.6, 4.8, 0.5, 0.02, CYAN) # Resolve -> Improve
    draw_connector_line(9.4, 4.1, 0.02, 0.3, CYAN) # Improve -> Automate
    draw_connector_line(9.7, 3.0, 0.5, 0.02, CYAN) # Automate -> Monitor

    # Footer banner
    draw_connector_line(0.4, 6.52, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.6, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.6, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


# ==========================================
# SLIDE 19 GENERATION
# ==========================================
def build_slide_19():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    r_t1 = p_title.add_run()
    r_t1.text = "OPERATIONAL KEY PERFORMANCE INDICATORS (KPIs)\n"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "KPI-Driven Governance Ensuring High Availability and Service Excellence"
    r_t2.font.name = "Arial"
    r_t2.font.size = Pt(11)
    r_t2.font.bold = True
    r_t2.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- KEY OPERATIONAL KPIs (Horizontal row of 7 columns) ---
    draw_card(0.4, 0.95, 12.53, 1.25, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 0.95, 12.53, 0.28, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 0.98, 12.33, 0.22, [{"text": "KEY OPERATIONAL KPIs", "bold": True, "size": 8.5, "color": GOLD}], PP_ALIGN.CENTER)

    kpis = [
        ("SERVICE AVAILABILITY", "> 99.5%", "Target", "icon_excellence.png", 0.5),
        ("MONITORING COVERAGE", "100%", "Target", "icon_excellence.png", 2.25),
        ("SLA COMPLIANCE", "> 99%", "Target", "icon_badge_w.png", 4.0),
        ("MTTR", "< 4 HRS", "Target", "icon_calendar_w.png", 5.75),
        ("CHANGE SUCCESS RATE", "> 95%", "Target", "icon_excellence.png", 7.5),
        ("CRITICAL VULNERABILITIES", "0", "Overdue", "icon_shield_w.png", 9.25),
        ("DEPLOYMENT SUCCESS RATE", "> 98%", "Target", "icon_rocket_w.png", 11.0)
    ]
    for idx, (title, val, status, icon_file, cx) in enumerate(kpis):
        if idx > 0:
            draw_connector_line(cx - 0.05, 1.3, 0.015, 0.8, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.1), Inches(1.35), Inches(0.24), Inches(0.24))
        except:
            pass
            
        add_text_box(cx + 0.38, 1.32, 1.32, 0.8, [
            {"text": title + "\n", "bold": True, "size": 6, "color": WHITE},
            {"text": val + "\n", "bold": True, "size": 11, "color": CYAN if idx != 5 else GOLD},
            {"text": status, "size": 6, "color": TEXT_MUTED}
        ])

    # --- BOTTOM SECTION: Enablers & Dedicated ODC ---
    # Left Card: Enablers
    draw_card(0.4, 2.3, 7.8, 4.0, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 2.3, 7.8, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 2.33, 7.6, 0.25, [{"text": "ENABLERS FOR EXCELLENCE", "bold": True, "size": 9, "color": WHITE}], PP_ALIGN.CENTER)

    enablers = [
        ("Secure\nInfrastructure", "Reliable and compliant physical & cloud host environments", "icon_shield_w.png", 0, 0),
        ("Skilled & Experienced\nAirbus Teams", "Domain experts with specialized operational readiness", "icon_group_w.png", 1, 0),
        ("Training &\nCertification", "Ongoing technical training & process certifications", "icon_diploma_w.png", 2, 0),
        ("AI-Enabled\nOperations", "Leveraging machine learning & automations for predictability", "icon_robot.png", 0, 1),
        ("Strong Governance\n& Collaboration", "Unified engagement models across IT & operations", "icon_group_w.png", 1, 1),
        ("Standardized Processes\n(ITIL, ISO 20000)", "ITIL aligned structures ensuring service continuity", "icon_excellence.png", 2, 1)
    ]
    for title, desc, icon_file, col, row in enablers:
        gx = 0.65 + col * 2.45
        gy = 2.75 + row * 1.7
        
        # Icon circle
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(gx + 0.9), Inches(gy), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(gx + 0.95), Inches(gy + 0.05), Inches(0.25), Inches(0.25))
        except:
            pass
            
        add_text_box(gx, gy + 0.4, 2.15, 1.2, [
            {"text": title + "\n", "bold": True, "size": 7.5, "color": GOLD},
            {"text": desc, "size": 6.8, "color": WHITE}
        ], PP_ALIGN.CENTER)

    # Right Card: Dedicated Secure Airbus ODC
    draw_card(8.4, 2.3, 4.5, 4.0, CARD_BG, BORDER_BLUE)
    draw_card(8.4, 2.3, 4.5, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.5, 2.33, 4.3, 0.25, [{"text": "DEDICATED SECURE AIRBUS ODC", "bold": True, "size": 9, "color": CYAN}], PP_ALIGN.CENTER)

    c_sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.45), Inches(2.78), Inches(0.55), Inches(0.55))
    c_sh.fill.solid()
    c_sh.fill.fore_color.rgb = RGBColor(12, 35, 75)
    c_sh.line.color.rgb = GOLD
    c_sh.line.width = Pt(0.8)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_shield_w.png"), Inches(10.55), Inches(2.88), Inches(0.35), Inches(0.35))
    except:
        pass
        
    odc_bullets = [
        "Segregated Physical Environment",
        "Strict RBAC & Need-to-know access control",
        "Airbus specific Security Training",
        "Export Control Awareness & Monitoring",
        "GDPR & Data Protection compliance",
        "Business continuity & Disaster Recovery ready"
    ]
    bullets_text = ""
    for b in odc_bullets:
        bullets_text += "• " + b + "\n"
    bullets_text = bullets_text.strip("\n")
    add_text_box(8.65, 3.45, 4.0, 2.7, [{"text": bullets_text, "size": 7.5, "color": WHITE}])

    # --- 6. BOTTOM-MOST BANNER ---
    draw_card(0.4, 6.42, 12.53, 0.5, CARD_BG, GOLD)
    
    footer_segments = [
        ("OUR COMMITMENT", "icon_excellence.png", 0.4),
        ("Quality", "icon_badge_w.png", 4.1),
        ("Security", "icon_shield_w.png", 6.2),
        ("Reliability", "icon_excellence.png", 8.3),
        ("Continuity", "icon_workflow_w.png", 10.4)
    ]
    
    for idx, (title, icon_file, cx) in enumerate(footer_segments):
        if idx > 0:
            draw_connector_line(cx, 6.47, 0.015, 0.4, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.12), Inches(6.52), Inches(0.28), Inches(0.28))
        except:
            pass
            
        tb = slide.shapes.add_textbox(Inches(cx + 0.45), Inches(6.48), Inches(1.8), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(7.5)
        r1.font.color.rgb = GOLD if idx == 0 else WHITE
        r1.font.name = "Arial"

    draw_connector_line(0.4, 6.95, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 7.02, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 7.02, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 20 GENERATION
# ==========================================
def build_slide_20():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    r_t1 = p_title.add_run()
    r_t1.text = "WP2 "
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "OPERATING MODEL & GOVERNANCE\n"
    r_t2.font.name = "Times New Roman"
    r_t2.font.size = Pt(28)
    r_t2.font.bold = True
    r_t2.font.color.rgb = WHITE
    
    r_t3 = p_title.add_run()
    r_t3.text = "Service Delivery Lead governing four operational towers supported by shared excellence functions and structured governance"
    r_t3.font.name = "Arial"
    r_t3.font.size = Pt(11)
    r_t3.font.bold = True
    r_t3.font.color.rgb = CYAN

    # Akkodis Logo in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # --- TOP ROW: Service Delivery Lead (SDL) ---
    draw_card(4.67, 0.95, 4.0, 0.8, CARD_BG, GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_people.png"), Inches(4.82), Inches(1.1), Inches(0.5), Inches(0.5))
    except:
        pass
    add_text_box(5.47, 1.1, 3.0, 0.6, [
        {"text": "SERVICE DELIVERY LEAD (SDL)\n", "bold": True, "size": 9.5, "color": GOLD},
        {"text": "Overall Accountability & Governance", "size": 8, "color": WHITE}
    ])

    # Connecting org-chart lines
    draw_connector_line(6.67, 1.75, 0.015, 0.25, BORDER_BLUE)
    draw_connector_line(1.85, 2.0, 9.63, 0.015, BORDER_BLUE)
    draw_connector_line(1.85, 2.0, 0.015, 0.2, BORDER_BLUE)
    draw_connector_line(5.06, 2.0, 0.015, 0.2, BORDER_BLUE)
    draw_connector_line(8.27, 2.0, 0.015, 0.2, BORDER_BLUE)
    draw_connector_line(11.48, 2.0, 0.015, 0.2, BORDER_BLUE)

    # --- Org Chart Tiers (Four Towers) ---
    towers = [
        ("WP2.1\nMONITORING (NOC)", "24x7 Monitoring\n& Event Management", "icon_excellence.png", 0.5, CYAN),
        ("WP2.2\nSERVICE SUPPORT", "IT Service Management\n& Support", "icon_chat_w.png", 3.71, BORDER_BLUE),
        ("WP2.3\nMAINTENANCE", "Engineering &\nContinuous Improvement", "icon_gear_w.png", 6.92, GREEN_BORDER),
        ("WP2.4\nPLATFORM SERVICES", "Platform Operations\n& Lifecycle Management", "icon_excellence.png", 10.13, RGBColor(120, 50, 150))
    ]
    for title, desc, icon_file, cx, col_theme in towers:
        draw_card(cx, 2.2, 2.7, 2.1, CARD_BG, col_theme)
        
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 1.1), Inches(2.32), Inches(0.5), Inches(0.5))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = col_theme
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 1.2), Inches(2.42), Inches(0.3), Inches(0.3))
        except:
            pass
            
        add_text_box(cx + 0.1, 2.92, 2.5, 0.5, [{"text": title, "bold": True, "size": 8.5, "color": col_theme}], PP_ALIGN.CENTER)
        add_text_box(cx + 0.1, 3.52, 2.5, 0.6, [{"text": desc, "size": 7.5, "color": WHITE}], PP_ALIGN.CENTER)

        # Arrows down to Shared Excellence layer
        draw_connector_line(cx + 1.35, 4.3, 0.015, 0.3, BORDER_BLUE)

    # --- SHARED EXCELLENCE & AUTOMATION LAYER ---
    draw_card(0.4, 4.6, 12.53, 0.92, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 4.62, 12.33, 0.22, [{"text": "SHARED EXCELLENCE & AUTOMATION LAYER", "bold": True, "size": 8.5, "color": CYAN}], PP_ALIGN.CENTER)

    excel_items = [
        ("AI Engineering\n& Automation", "icon_robot.png", 0.5),
        ("QA &\nProcess", "icon_shield_w.png", 3.0),
        ("Knowledge\nManagement", "icon_diploma_w.png", 5.5),
        ("Reporting &\nAnalytics", "icon_excellence.png", 8.0),
        ("Training &\nEnablement", "icon_excellence.png", 10.5)
    ]
    for idx, (name, icon_file, cx) in enumerate(excel_items):
        if idx > 0:
            draw_connector_line(cx - 0.05, 4.92, 0.015, 0.5, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(4.92), Inches(0.3), Inches(0.3))
        except:
            pass
        add_text_box(cx + 0.55, 4.92, 1.8, 0.45, [{"text": name, "bold": True, "size": 7.5, "color": WHITE}])

    # Connecting arrow to Governance layer
    draw_connector_line(6.67, 5.52, 0.015, 0.18, BORDER_BLUE)

    # --- GOVERNANCE & SERVICE REVIEWS ---
    draw_card(0.4, 5.7, 12.53, 0.95, CARD_BG, BORDER_BLUE)
    add_text_box(0.5, 5.72, 12.33, 0.22, [{"text": "GOVERNANCE & SERVICE REVIEWS", "bold": True, "size": 8.5, "color": GOLD}], PP_ALIGN.CENTER)

    govs = [
        ("DAILY", "Operations &\nIncident Review", "icon_calendar_w.png", 0.5),
        ("WEEKLY", "SLA, Incidents &\nChange Review", "icon_excellence.png", 3.6),
        ("MONTHLY", "Service Review,\nKPI & Forecast", "icon_gear_w.png", 6.7),
        ("QUARTERLY", "QBR, Maturity\n& Roadmap Review", "icon_excellence.png", 9.8)
    ]
    for idx, (g_title, g_desc, icon_file, cx) in enumerate(govs):
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx + 0.1), Inches(6.02), Inches(0.35), Inches(0.35))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(6.07), Inches(0.25), Inches(0.25))
        except:
            pass
            
        add_text_box(cx + 0.55, 6.02, 2.4, 0.55, [
            {"text": g_title + "\n", "bold": True, "size": 7.5, "color": GOLD},
            {"text": g_desc, "size": 6.8, "color": WHITE}
        ])

        if idx < 3:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(cx + 2.75), Inches(6.12), Inches(0.2), Inches(0.12))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # --- 6. BOTTOM-MOST BANNER ---
    draw_card(0.4, 6.72, 12.53, 0.45, CARD_BG, GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(0.55), Inches(6.78), Inches(0.24), Inches(0.24))
    except:
        pass
    add_text_box(0.85, 6.78, 12.0, 0.35, [
        {"text": "FOCUS: 99.9% UPTIME  |  95% SLA  |  AI-ENABLED OPERATIONS  |  ITIL V4 MATURITY  |  24x7 EXCELLENCE  |  SEAMLESS INTEGRATION WITH WP1 & WP3", "bold": True, "size": 7.5, "color": GOLD}
    ])

    draw_connector_line(0.4, 7.22, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 7.26, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 7.26, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)



# ==========================================
# SLIDE 21 GENERATION
# ==========================================
def build_slide_21():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # 1. Slide Title (Times New Roman 28pt)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(9.5), Inches(0.8))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    r_t1 = p_title.add_run()
    r_t1.text = "WP3 "
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = True
    r_t1.font.color.rgb = GOLD
    
    r_t2 = p_title.add_run()
    r_t2.text = "- DELIVERING SUSTAINABLE VALUE & IMPACT\n"
    r_t2.font.name = "Times New Roman"
    r_t2.font.size = Pt(28)
    r_t2.font.bold = True
    r_t2.font.color.rgb = WHITE
    
    r_t3 = p_title.add_run()
    r_t3.text = "A Scalable, Secure & Adaptive Delivery Model Aligning to Airbus Priorities"
    r_t3.font.name = "Arial"
    r_t3.font.size = Pt(11)
    r_t3.font.bold = True
    r_t3.font.color.rgb = CYAN

    # Airbus & Akkodis Logos in top right
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_airbus.png"), Inches(10.0), Inches(0.25), Inches(1.2), Inches(0.3))
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(11.4), Inches(0.25), Inches(1.5), Inches(0.3))
    except:
        pass

    # Airbus plane background illustration
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide13_header_bg.png"), Inches(6.8), Inches(0.12), Inches(2.2), Inches(0.75))
    except:
        pass

    # --- COLUMN 1: Hot Topics We Understand (Vertical list) ---
    draw_card(0.4, 0.95, 3.9, 4.8, CARD_BG, BORDER_BLUE)
    draw_card(0.4, 0.95, 3.9, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(0.5, 0.98, 3.7, 0.25, [{"text": "HOT TOPICS WE UNDERSTAND", "bold": True, "size": 8.5, "color": WHITE}], PP_ALIGN.CENTER)

    hot_topics = [
        ("AI & LLM ENABLEMENT", "AI-ready knowledge repos / GenAI compliance", "icon_excellence.png"),
        ("SAFe & AGILE AT SCALE", "SAFe 6.0 across ARTs & PI planning", "icon_group_w.png"),
        ("DEVSECOPS & AUTOMATION", "CI/CD & secure software delivery", "icon_rocket_w.png"),
        ("INDUSTRIAL DIGITALIZATION", "SCADA, Kafka, MQM & Smart Factory", "icon_excellence.png"),
        ("SECURITY & COMPLIANCE", "GDPR, Export Control & data handling", "icon_shield_w.png"),
        ("OPERATIONAL EXCELLENCE", "SLA-driven support model & MIM", "icon_gear_w.png"),
        ("KNOWLEDGE & SHIFT-LEFT", "AI-enabled Knowledge Base & self-service", "icon_diploma_w.png"),
        ("CONTINUOUS IMPROVEMENT", "KPI-driven service optimization & automations", "icon_excellence.png")
    ]
    for idx, (title, desc, icon_file) in enumerate(hot_topics):
        y_pos = 1.35 + idx * 0.54
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(0.55), Inches(y_pos), Inches(0.24), Inches(0.24))
        except:
            pass
        add_text_box(0.88, y_pos - 0.04, 3.3, 0.2, [{"text": title, "bold": True, "size": 7, "color": CYAN}])
        add_text_box(0.88, y_pos + 0.16, 3.3, 0.35, [{"text": desc, "size": 6.2, "color": WHITE}])
        if idx < 7:
            draw_connector_line(0.5, y_pos + 0.5, 3.7, 0.01, BORDER_BLUE)

    # --- COLUMN 2: Adaptability Framework (Vertical Flow) ---
    draw_card(4.5, 0.95, 3.9, 4.8, CARD_BG, BORDER_BLUE)
    draw_card(4.5, 0.95, 3.9, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(4.6, 0.98, 3.7, 0.25, [{"text": "ADAPTABILITY FRAMEWORK", "bold": True, "size": 8.5, "color": WHITE}], PP_ALIGN.CENTER)

    # Card 1: Secure Delivery Center
    draw_card(4.6, 1.35, 3.7, 1.15, CARD_BG, BORDER_BLUE)
    add_text_box(4.65, 1.37, 3.6, 0.2, [{"text": "SECURE AIRBUS DELIVERY CENTER", "bold": True, "size": 7, "color": GOLD}], PP_ALIGN.CENTER)
    bullets_odc = "• Segregated delivery organization  • Trained & certified resources\n• Security compliance  • Export Control & GDPR  • Business continuity"
    add_text_box(4.65, 1.58, 3.6, 0.9, [{"text": bullets_odc, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)

    # Down Arrow
    arrow1 = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(6.35), Inches(2.52), Inches(0.18), Inches(0.1))
    arrow1.fill.solid()
    arrow1.fill.fore_color.rgb = BORDER_BLUE
    arrow1.line.fill.background()

    # Card 2: Business Demand
    draw_card(4.6, 2.65, 3.7, 0.65, CARD_BG, BORDER_BLUE)
    add_text_box(4.65, 2.67, 3.6, 0.2, [{"text": "BUSINESS DEMAND & PRIORITY MANAGEMENT", "bold": True, "size": 7, "color": GOLD}], PP_ALIGN.CENTER)
    bullets_demand = "• Agile response to priorities  • Integrated planning & governance"
    add_text_box(4.65, 2.87, 3.6, 0.4, [{"text": bullets_demand, "size": 6, "color": WHITE}], PP_ALIGN.CENTER)

    # Down Arrow
    arrow2 = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(6.35), Inches(3.32), Inches(0.18), Inches(0.1))
    arrow2.fill.solid()
    arrow2.fill.fore_color.rgb = BORDER_BLUE
    arrow2.line.fill.background()

    # Card 3: Flexible Delivery Models
    draw_card(4.6, 3.45, 3.7, 1.15, CARD_BG, BORDER_BLUE)
    add_text_box(4.65, 3.47, 3.6, 0.2, [{"text": "FLEXIBLE DELIVERY MODELS (SAFe | Scrum | Waterfall)", "bold": True, "size": 7, "color": CYAN}], PP_ALIGN.CENTER)
    
    add_text_box(4.65, 3.67, 1.2, 0.9, [
        {"text": "SAFe\n", "bold": True, "size": 6.5, "color": GOLD},
        {"text": "• ART delivery\n• PI Planning", "size": 5.8, "color": WHITE}
    ])
    draw_connector_line(5.82, 3.7, 0.01, 0.8, BORDER_BLUE)
    add_text_box(5.85, 3.67, 1.2, 0.9, [
        {"text": "Agile Scrum\n", "bold": True, "size": 6.5, "color": GOLD},
        {"text": "• Sprint execution\n• Rapid iterations", "size": 5.8, "color": WHITE}
    ])
    draw_connector_line(7.07, 3.7, 0.01, 0.8, BORDER_BLUE)
    add_text_box(7.1, 3.67, 1.15, 0.9, [
        {"text": "Waterfall\n", "bold": True, "size": 6.5, "color": GOLD},
        {"text": "• Structured gov\n• Milestone deliv", "size": 5.8, "color": WHITE}
    ])

    # Down Arrow
    arrow3 = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(6.35), Inches(4.62), Inches(0.18), Inches(0.1))
    arrow3.fill.solid()
    arrow3.fill.fore_color.rgb = BORDER_BLUE
    arrow3.line.fill.background()

    # Bottom 3 small blocks linked by arrows
    by = 4.75
    draw_card(4.6, by, 1.15, 0.9, CARD_BG, BORDER_BLUE)
    add_text_box(4.62, by + 0.05, 1.11, 0.8, [
        {"text": "DEVSECOPS & QE\n", "bold": True, "size": 5.8, "color": GOLD},
        {"text": "• Auto testing\n• Auto deploy\n• Code quality", "size": 5.2, "color": WHITE}
    ])

    arrow_r1 = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(5.8), Inches(by + 0.35), Inches(0.08), Inches(0.15))
    arrow_r1.fill.solid()
    arrow_r1.fill.fore_color.rgb = BORDER_BLUE
    arrow_r1.line.fill.background()

    draw_card(5.9, by, 1.1, 0.9, CARD_BG, BORDER_BLUE)
    add_text_box(5.92, by + 0.05, 1.06, 0.8, [
        {"text": "KNOWLEDGE OPS\n", "bold": True, "size": 5.8, "color": GOLD},
        {"text": "• Shift-left model\n• AI/LLM repos\n• Retention", "size": 5.2, "color": WHITE}
    ])

    arrow_r2 = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(7.05), Inches(by + 0.35), Inches(0.08), Inches(0.15))
    arrow_r2.fill.solid()
    arrow_r2.fill.fore_color.rgb = BORDER_BLUE
    arrow_r2.line.fill.background()

    draw_card(7.15, by, 1.15, 0.9, CARD_BG, BORDER_BLUE)
    add_text_box(7.17, by + 0.05, 1.11, 0.8, [
        {"text": "CONTINUOUS CSI\n", "bold": True, "size": 5.8, "color": GOLD},
        {"text": "• KPI governance\n• Automation\n• Efficiency gains", "size": 5.2, "color": WHITE}
    ])

    # --- COLUMN 3: Key Business Outcomes (Vertical list) ---
    draw_card(8.6, 0.95, 4.3, 4.8, CARD_BG, BORDER_BLUE)
    draw_card(8.6, 0.95, 4.3, 0.32, RGBColor(12, 35, 75), BORDER_BLUE)
    add_text_box(8.7, 0.98, 4.1, 0.25, [{"text": "KEY BUSINESS OUTCOMES", "bold": True, "size": 8.5, "color": WHITE}], PP_ALIGN.CENTER)

    outcomes = [
        "Faster Time to Market",
        "Higher Quality & Reliability",
        "Improved Operational Resilience",
        "Reduced Incidents & Faster Recovery",
        "Optimized Cost & Efficiency",
        "Enhanced User Experience",
        "Improved Compliance & Security",
        "Sustainable Digital Transformation"
    ]
    for idx, name in enumerate(outcomes):
        y_pos = 1.35 + idx * 0.54
        # Green checkmark circle badge
        chk = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.8), Inches(y_pos + 0.02), Inches(0.18), Inches(0.18))
        chk.fill.solid()
        chk.fill.fore_color.rgb = GREEN_BORDER
        chk.line.fill.background()
        add_text_box(8.8, y_pos, 0.18, 0.18, [{"text": "\u2714", "bold": True, "size": 5.5, "color": WHITE}], PP_ALIGN.CENTER)
        
        add_text_box(9.05, y_pos - 0.02, 3.7, 0.3, [{"text": name, "bold": True, "size": 7.5, "color": WHITE}])
        if idx < 7:
            draw_connector_line(8.7, y_pos + 0.5, 4.1, 0.01, BORDER_BLUE)

    # --- BOTTOM SECTION: OUTCOMES PROGRESSION BANNER ---
    draw_card(0.4, 5.85, 12.53, 0.85, CARD_BG, GOLD)
    
    outcomes_footer = [
        ("FOCUS ON IMPACT", "icon_excellence.png", 0.5),
        ("DRIVE EFFICIENCY", "icon_excellence.png", 2.6),
        ("DELIVER QUALITY", "icon_gear_w.png", 4.7),
        ("ENSURE SECURITY", "icon_shield_w.png", 6.8),
        ("ACCELERATE DELIVERY", "icon_excellence.png", 8.9),
        ("CREATE VALUE", "icon_group_w.png", 11.0)
    ]
    for idx, (title, icon_file, cx) in enumerate(outcomes_footer):
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.4), Inches(5.92), Inches(0.28), Inches(0.28))
        except:
            pass
        add_text_box(cx, 6.32, 1.1, 0.3, [{"text": title, "bold": True, "size": 7.5, "color": GOLD}], PP_ALIGN.CENTER)

        if idx < 5:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(cx + 1.6), Inches(6.12), Inches(0.2), Inches(0.12))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = BORDER_BLUE
            arrow.line.fill.background()

    # Slide footer text at the very bottom
    draw_connector_line(0.4, 6.85, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.9, 5.0, 0.25, [{"text": "Right Training. Right Start. Right Impact.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.9, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


# ==========================================
# SLIDE 22 GENERATION
# ==========================================
def build_slide_22():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # Akkodis Logo in top left
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(0.4), Inches(0.2), Inches(1.5), Inches(0.3))
    except:
        pass

    # Top header text: "DRIVING INNOVATION. DELIVERING EXCELLENCE."
    add_text_box(4.5, 0.2, 4.3, 0.3, [{"text": "DRIVING INNOVATION. DELIVERING EXCELLENCE.", "bold": True, "size": 9, "color": GOLD}])

    # 1. Slide Title (Times New Roman 28pt, NOT BOLD, Title Case)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.6), Inches(12.53), Inches(0.5))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    r_t1 = p_title.add_run()
    r_t1.text = "Automotive Engineering & CAE Simulation Capabilities"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = False
    r_t1.font.color.rgb = WHITE

    # Subtitle: "Interior | Exterior | CAE Simulation"
    add_text_box(0.4, 1.15, 12.53, 0.3, [{"text": "Interior  |  Exterior  |  CAE Simulation", "bold": True, "size": 11, "color": CYAN}])

    # --- THREE VERTICAL COLUMNS ---
    card_y = 1.6
    card_h = 3.9
    card_w = 3.9
    
    # Column 1: Interior Engineering
    draw_card(0.4, card_y, card_w, card_h, CARD_BG, BORDER_BLUE)
    # Circle icon
    circ1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(2.0), Inches(1.75), Inches(0.7), Inches(0.7))
    circ1.fill.solid()
    circ1.fill.fore_color.rgb = RGBColor(12, 35, 75)
    circ1.line.color.rgb = GOLD
    circ1.line.width = Pt(1)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(2.18), Inches(1.93), Inches(0.34), Inches(0.34))
    except:
        pass
    add_text_box(0.5, 2.55, 3.7, 0.3, [{"text": "INTERIOR ENGINEERING", "bold": True, "size": 9.5, "color": GOLD}], PP_ALIGN.CENTER)
    bullets1 = "\u2022  Concept & Detailed Design\n\u2022  Instrument Panel & Consoles\n\u2022  Door Trim, IP, Cockpit Modules\n\u2022  HMI / UX & Ergonomics\n\u2022  Materials, CMF & Surface Styling\n\u2022  DFM & Packaging Optimization"
    add_text_box(0.65, 2.95, 3.4, 2.4, [{"text": bullets1, "size": 8.5, "color": WHITE}])

    # Column 2: Exterior Engineering
    draw_card(4.7, card_y, card_w, card_h, CARD_BG, BORDER_BLUE)
    circ2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.3), Inches(1.75), Inches(0.7), Inches(0.7))
    circ2.fill.solid()
    circ2.fill.fore_color.rgb = RGBColor(12, 35, 75)
    circ2.line.color.rgb = CYAN
    circ2.line.width = Pt(1)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_process_w.png"), Inches(6.48), Inches(1.93), Inches(0.34), Inches(0.34))
    except:
        pass
    add_text_box(4.8, 2.55, 3.7, 0.3, [{"text": "EXTERIOR ENGINEERING", "bold": True, "size": 9.5, "color": CYAN}], PP_ALIGN.CENTER)
    bullets2 = "\u2022  Concept to Production Design\n\u2022  Class-A Surfacing & Styling\n\u2022  BIW / Closures / Aerodynamics\n\u2022  Lighting (Exterior) & Grille Design\n\u2022  Trim, Moldings & Accessories\n\u2022  Digital Mockup & Visualization"
    add_text_box(4.95, 2.95, 3.4, 2.4, [{"text": bullets2, "size": 8.5, "color": WHITE}])

    # Column 3: CAE & Simulation
    draw_card(9.0, card_y, card_w, card_h, CARD_BG, BORDER_BLUE)
    circ3 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.6), Inches(1.75), Inches(0.7), Inches(0.7))
    circ3.fill.solid()
    circ3.fill.fore_color.rgb = RGBColor(12, 35, 75)
    circ3.line.color.rgb = WHITE
    circ3.line.width = Pt(1)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_gear_w.png"), Inches(10.78), Inches(1.93), Inches(0.34), Inches(0.34))
    except:
        pass
    add_text_box(9.1, 2.55, 3.7, 0.3, [{"text": "CAE & SIMULATION", "bold": True, "size": 9.5, "color": WHITE}], PP_ALIGN.CENTER)
    bullets3 = "\u2022  Structural (FEA) & NVH Analysis\n\u2022  Crashworthiness (Frontal, Side, Rear)\n\u2022  Occupant Safety (Dummy, Airbag)\n\u2022  Durability & Fatigue Analysis\n\u2022  CFD (Aero, Thermal, HVAC)\n\u2022  Optimization & Design Validation"
    add_text_box(9.25, 2.95, 3.4, 2.4, [{"text": bullets3, "size": 8.5, "color": WHITE}])

    # --- BOTTOM SECTION: ENABLERS CARD ---
    draw_card(0.4, 5.65, 12.53, 0.9, CARD_BG, GOLD)
    
    enablers = [
        ("END-TO-END CAPABILITIES", "From Concept to Production", "icon_excellence.png", 0.4),
        ("GLOBAL EXPERTISE", "Skilled Teams, Global Delivery", "icon_people.png", 3.53),
        ("INNOVATION LED", "Digital, AI & Next Gen Tools", "icon_excellence.png", 6.66),
        ("QUALITY & RELIABILITY", "Robust Processes, On-time Delivery", "icon_shield_w.png", 9.79)
    ]
    
    slot_w = 12.53 / 4.0
    for idx, (title, desc, icon_file, cx) in enumerate(enablers):
        if idx > 0:
            draw_connector_line(cx, 5.7, 0.015, 0.8, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(5.82), Inches(0.28), Inches(0.28))
        except:
            pass
            
        add_text_box(cx + 0.5, 5.75, slot_w - 0.6, 0.7, [
            {"text": title + "\n", "bold": True, "size": 7.5, "color": GOLD},
            {"text": desc, "size": 6.8, "color": WHITE}
        ])

    # Slide footer text at the very bottom
    draw_connector_line(0.4, 6.7, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.78, 6.0, 0.25, [{"text": "POWERING INTELLIGENT MOBILITY. TOGETHER.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.78, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


# ==========================================
# SLIDE 23 GENERATION
# ==========================================
def build_slide_23():
    # Dynamic crop logic for central cockpit image
    try:
        import os
        from PIL import Image
        brain_dir = r"C:\Users\Akshay.JOHN-XAVIER\.\gemini\antigravity-ide\brain\90927278-bd0d-48cf-b562-bc44917b61b1"
        if not os.path.exists(brain_dir):
            brain_dir = r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\90927278-bd0d-48cf-b562-bc44917b61b1"
        files = [f for f in os.listdir(brain_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        files_with_time = [(f, os.path.getmtime(os.path.join(brain_dir, f))) for f in files]
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        if files_with_time:
            latest_file = os.path.join(brain_dir, files_with_time[0][0])
            with Image.open(latest_file) as img:
                width, height = img.size
                left = int(width * 0.20)
                top = int(height * 0.35)
                right = int(width * 0.80)
                bottom = int(height * 0.72)
                cockpit_img = img.crop((left, top, right, bottom))
                output_path = r"c:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Icons\slide23_cockpit.png"
                cockpit_img.save(output_path)
                print("Successfully cropped cockpit image dynamically.")
    except Exception as e:
        print("Dynamic cropping error:", e)

    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    
    # --- HELPER FUNCTIONS ---
    def draw_card(l, t, w, h, bg, border, bw=1):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg
        if border:
            sh.line.color.rgb = border
            sh.line.width = Pt(bw)
        else:
            sh.line.fill.background()
        try:
            sh.adjustments[0] = 0.04
        except:
            pass
        return sh

    def add_text_box(l, t, w, h, text_runs, align=PP_ALIGN.LEFT, word_wrap=True):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        
        for idx, run_data in enumerate(text_runs):
            txt = run_data.get("text", "")
            bold = run_data.get("bold", False)
            size = run_data.get("size", 9)
            color = run_data.get("color", WHITE)
            font_name = run_data.get("font", "Arial")
            
            if idx == 0:
                run = p.add_run() if p.text else p
                if hasattr(run, 'add_run'):
                    run.text = txt
                else:
                    p.text = txt
                    run = p
            else:
                run = p.add_run()
                run.text = txt
                
            run.font.bold = bold
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = font_name
            
        return tb

    def draw_connector_line(l, t, w, h, col=BORDER_BLUE):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
        line.fill.solid()
        line.fill.fore_color.rgb = col
        line.line.fill.background()
        return line

    icons_dir = r"c:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/Redesign with Design System/Icons"

    # Akkodis Logo in top left
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "logo_akkodis_white.png"), Inches(0.4), Inches(0.2), Inches(1.5), Inches(0.3))
    except:
        pass

    # 1. Slide Title (Times New Roman 28pt, NOT BOLD, Title Case)
    titleBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.6), Inches(12.53), Inches(0.5))
    tf_title = titleBox.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    r_t1 = p_title.add_run()
    r_t1.text = "Automotive Interior Engineering"
    r_t1.font.name = "Times New Roman"
    r_t1.font.size = Pt(28)
    r_t1.font.bold = False
    r_t1.font.color.rgb = WHITE

    # Subtitle
    add_text_box(0.4, 1.15, 12.53, 0.3, [{"text": "End-to-End Capability Across Design, Engineering & Validation", "bold": True, "size": 11, "color": CYAN}])

    # --- MIDDLE SECTION: Cockpit Image & Steps ---
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "slide23_cockpit.png"), Inches(2.97), Inches(2.1), Inches(7.4), Inches(2.7))
    except:
        pass

    # Inside middle text banner
    add_text_box(4.8, 1.72, 3.7, 0.5, [
        {"text": "Designing Experiences. ", "bold": True, "size": 9.5, "color": WHITE},
        {"text": "Engineering Excellence. \\n", "bold": True, "size": 9.5, "color": CYAN},
        {"text": "Delivering Value.", "bold": True, "size": 9.5, "color": GOLD}
    ], PP_ALIGN.CENTER)

    # 9 Steps positioned around the cockpit image
    steps_data = [
        ("01", "STYLING SURFACE", "Class-A surfacing\\n& design intent", 0.4, 3.5),
        ("02", "ERGONOMICS & REGULATORY", "Reachability, visibility,\\ncomfort & safety", 1.0, 2.2),
        ("03", "VEHICLE INTEGRATION", "Cockpit, HVAC, EE\\n& system integration", 2.6, 1.35),
        ("04", "MASTER SECTIONS", "2D/3D sections,\\npackaging & clearance", 5.6, 1.35),
        ("05", "DIGITAL VALIDATION", "DFMEA, DFM/DFA,\\ntolerance & risk", 8.4, 1.35),
        ("06", "CAE & SIMULATION", "Structural, Crash, NVH,\\nDurability & Thermal", 10.0, 2.2),
        ("07", "TOOLING DESIGN", "Molds, fixtures\\n& manufacturing", 10.8, 3.5),
        ("08", "PROTOTYPE SUPPORT", "3D printing, soft tool,\\nprototyping support", 9.8, 4.5),
        ("09", "PRODUCTION RELEASE", "3D models, Drawings,\\nBOM, MBD & docs", 1.2, 4.5)
    ]
    for num, title, desc, sx, sy in steps_data:
        # Mini Step Badge
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(sx + 0.1), Inches(sy), Inches(0.24), Inches(0.24))
        circ.fill.solid()
        circ.fill.fore_color.rgb = RGBColor(12, 35, 75)
        circ.line.color.rgb = CYAN
        circ.line.width = Pt(0.7)
        add_text_box(sx + 0.1, sy - 0.02, 0.24, 0.24, [{"text": num, "bold": True, "size": 6.8, "color": GOLD}], PP_ALIGN.CENTER)

        add_text_box(sx + 0.42, sy - 0.04, 2.0, 0.2, [{"text": title, "bold": True, "size": 7, "color": CYAN}])
        add_text_box(sx + 0.42, sy + 0.16, 2.0, 0.45, [{"text": desc, "size": 6.2, "color": WHITE}])

    # --- BOTTOM SECTION: ENABLERS CARD ---
    draw_card(0.4, 5.4, 12.53, 0.85, CARD_BG, BORDER_BLUE)
    
    enablers = [
        ("EXPERT TEAMS", "Domain experts with deep automotive experience", "icon_people.png", 0.4),
        ("INNOVATION LED", "Digital tools, automation & next-gen engineering", "icon_excellence.png", 3.53),
        ("GLOBAL DELIVERY", "Scalable, agile & efficient delivery across time zones", "icon_excellence.png", 6.66),
        ("QUALITY ASSURED", "Standard processes, best practices & continuous improvement", "icon_shield_w.png", 9.79)
    ]
    slot_w = 12.53 / 4.0
    for idx, (title, desc, icon_file, cx) in enumerate(enablers):
        if idx > 0:
            draw_connector_line(cx, 5.45, 0.015, 0.75, BORDER_BLUE)
            
        try:
            slide.shapes.add_picture(os.path.join(icons_dir, icon_file), Inches(cx + 0.15), Inches(5.55), Inches(0.26), Inches(0.26))
        except:
            pass
            
        add_text_box(cx + 0.48, 5.48, slot_w - 0.55, 0.65, [
            {"text": title + "\\n", "bold": True, "size": 7.5, "color": GOLD},
            {"text": desc, "size": 6.5, "color": WHITE}
        ])

    # --- BOTTOM-MOST BANNER ---
    draw_card(0.4, 6.32, 12.53, 0.45, CARD_BG, GOLD)
    try:
        slide.shapes.add_picture(os.path.join(icons_dir, "icon_excellence.png"), Inches(0.55), Inches(6.38), Inches(0.24), Inches(0.24))
    except:
        pass
    add_text_box(0.85, 6.38, 12.0, 0.35, [
        {"text": "ONE PARTNER FOR COMPLETE INTERIOR ENGINEERING NEEDS  |  DESIGN EXCELLENCE  |  ENGINEERING PRECISION  |  SIMULATION INTELLIGENCE  |  MANUFACTURING READY", "bold": True, "size": 7.5, "color": GOLD}
    ])

    # Slide footer text at the very bottom
    draw_connector_line(0.4, 6.82, 12.5, 0.015, BORDER_BLUE)
    add_text_box(0.4, 6.88, 6.0, 0.25, [{"text": "POWERING INTELLIGENT MOBILITY. TOGETHER.", "bold": True, "size": 9, "color": GOLD}])
    add_text_box(7.9, 6.88, 5.0, 0.25, [{"text": "NPDM Excellence, Delivered.", "bold": True, "size": 9, "color": GOLD}], PP_ALIGN.RIGHT)


# Build and save
build_slide_1()
build_slide_2()
build_slide_3()
build_slide_4()
build_slide_5()
build_slide_6()
build_slide_7()
build_slide_8()
build_slide_9()
build_slide_10()
build_slide_11()
build_slide_12()
build_slide_13()
build_slide_14()
build_slide_16()
build_slide_17()
build_slide_18()
build_slide_19()
build_slide_20()
build_slide_21()
build_slide_22()
build_slide_23()

output_file = r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\Framework_Performance_Redesign.pptx"
prs.save(output_file)
print("PPTX deck generated successfully at:", output_file)
