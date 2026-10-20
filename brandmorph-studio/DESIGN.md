---
name: Industrial Lab Aesthetic
colors:
  surface: '#fbf9fa'
  surface-dim: '#dcd9db'
  surface-bright: '#fbf9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f4'
  surface-container: '#f0edee'
  surface-container-high: '#eae7e9'
  surface-container-highest: '#e4e2e3'
  on-surface: '#1b1b1d'
  on-surface-variant: '#44474c'
  inverse-surface: '#303031'
  inverse-on-surface: '#f3f0f1'
  outline: '#75777c'
  outline-variant: '#c5c6cc'
  surface-tint: '#535f70'
  primary: '#0e1a28'
  on-primary: '#ffffff'
  primary-container: '#232f3e'
  on-primary-container: '#8a97a9'
  inverse-primary: '#bbc7db'
  secondary: '#8a5100'
  on-secondary: '#ffffff'
  secondary-container: '#fe9800'
  on-secondary-container: '#643900'
  tertiary: '#101a26'
  on-tertiary: '#ffffff'
  tertiary-container: '#252f3c'
  on-tertiary-container: '#8c97a6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d7e3f7'
  primary-fixed-dim: '#bbc7db'
  on-primary-fixed: '#101c2b'
  on-primary-fixed-variant: '#3c4858'
  secondary-fixed: '#ffdcbd'
  secondary-fixed-dim: '#ffb86f'
  on-secondary-fixed: '#2c1600'
  on-secondary-fixed-variant: '#693c00'
  tertiary-fixed: '#d9e3f4'
  tertiary-fixed-dim: '#bdc7d8'
  on-tertiary-fixed: '#121c28'
  on-tertiary-fixed-variant: '#3e4755'
  background: '#fbf9fa'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e3'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  technical-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.5'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  max-container: 1800px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  section-gap: 120px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is engineered for a Design Technologist showcase, specifically tailored for the Amazon Brand Innovation Lab context. The personality is **Technically Rigorous**, **Editorial**, and **Premium**. It balances the precision of an engineering document with the sophisticated layout of a high-end design journal.

The style is a blend of **Modern Minimalism** and **Industrial Systematic**. It avoids unnecessary decoration, instead using "safety orange" accents and structural borders to guide the eye. The emotional response should be one of extreme competence—conveying that the creator can both ideate at a high level and execute with technical perfection.

Key aesthetic drivers:
- **Paper-like surfaces:** Using warm off-whites to reduce digital eye strain and evoke a "lab notebook" feel.
- **Technical detailing:** Small labels, monospaced data points, and hair-line borders that suggest a blueprint or schematic.
- **Controlled Vibe:** High whitespace to emphasize the quality of individual portfolio pieces.

## Colors

The palette is anchored in professional stability with strategic high-visibility accents.

- **Amazon Navy (#232F3E):** Used for primary headings, navigation backgrounds, and deep structural elements. It provides the "Executive" anchor.
- **Amazon Orange (#FF9900):** Used sparingly as a "Safety/Action" color. Reserved for primary CTAs, active states, and critical technical highlights.
- **Surface Warm (#FDFCFB):** The foundational background color. It provides a tactile, "paper" quality that distinguishes the site from generic white-box SaaS templates.
- **Surface Card (#FFFFFF):** Pure white used for content containers to create a subtle lift against the warm background.
- **Text Primary (#1A1A1A):** Near-black for maximum readability.
- **Text Muted (#4B5563):** Used for metadata, technical labels, and secondary descriptions.

## Typography

This design system utilizes a dual-font strategy to signal both "Design" and "Technology" roles.

1.  **Inter:** The workhorse for all primary communication. It is set with tight letter-spacing for headlines to create a bespoke, editorial look and standard spacing for body copy to ensure legibility.
2.  **JetBrains Mono:** Used for "Technical Tokens." This includes code snippets, build versions, project metadata (e.g., `Date: 2024.03.12`), and AI-related labels.

**Editorial Scaling:** Headlines should use a high scale ratio. Display text is significantly larger than body text to create a clear hierarchy and visual impact on the large 1800px grid.

## Layout & Spacing

The layout philosophy follows a **Fixed-Max Fluid Grid**. The content is contained within an expansive 1800px max-width, allowing for wide technical schematics and large-scale imagery typical of a showcase.

- **Grid Model:** A 12-column grid for desktop.
- **Sectioning:** Large vertical gaps (120px+) separate major case studies to allow each piece "room to breathe."
- **Sidebars:** Technical meta-data (tools used, role, timeline) should be placed in a 3-column side rail or a dedicated technical header for each project.
- **Breakpoints:**
  - **Desktop (1440px+):** Full 12-column spread with 64px margins.
  - **Tablet (768px - 1439px):** 8-column grid, margins reduced to 32px.
  - **Mobile (< 767px):** 4-column grid, margins 20px. Stack technical metadata vertically.

## Elevation & Depth

This design system avoids traditional heavy shadows in favor of **Tonal Layering and Technical Outlines.**

- **The Ground:** The `surfaceWarm` background is the lowest level.
- **The Card:** Project cards and code blocks use `surfaceCard` (white) with a hairline border (`1px solid #E5E7EB`). 
- **The Lift:** Instead of a shadow, use a slight translation (e.g., moving an element 4px up and right) or a very subtle, sharp "industrial" shadow (4px 4px 0px rgba(0,0,0,0.05)) to indicate interactivity.
- **The Overlay:** Modal overlays or dropdowns use a sharp 1px border in `amazonNavy` to maintain the blueprint aesthetic.

## Shapes

The shape language is **Soft yet Structured**. 

A `roundedness: 1` (4px base) is applied to keep the interface feeling modern and approachable without losing the professional "edge" required for a technical showcase. 

- **Buttons & Inputs:** 4px radius.
- **Project Cards:** 8px radius (Large) to differentiate them from smaller technical elements.
- **Code Blocks:** 4px radius to match the technical precision of the typography.
- **Tag/Chips:** Fully pill-shaped (100px) to provide a soft contrast to the otherwise rectilinear grid.

## Components

### Buttons
- **Primary:** `amazonOrange` background, `amazonNavy` or `White` text. Bold, 14px uppercase label.
- **Secondary:** `amazonNavy` border (1px), transparent background.
- **Technical Action:** Small (32px height) button using `JetBrains Mono` text, indicating a utility function like "Copy Code" or "View Repo."

### Cards
- Portfolio items should use a "Technical Sheet" style: Image on top, followed by a hairline divider, then a metadata row (using `technical-md` font) before the project title.

### Chips & Tags
- Used for tech-stack indicators. Subtle grey background (`#F3F4F6`) with `technical-md` text. No borders.

### Input Fields
- Underlined style or subtle 1px gray border. Focused state uses an `amazonOrange` bottom border (2px).

### Technical Callouts
- Specialized containers for AI/Code snippets. Use a dark `amazonNavy` background with neon-tinted syntax highlighting to contrast against the otherwise warm, light UI.