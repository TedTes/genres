-- =========================================================
-- Seed 15 base resume templates
-- =========================================================

insert into public.resume_templates (id, name, tier, engine, ats_strict, layout,
  supported_sections, design_tokens, capabilities, print_options, skeleton_handle, active_version, changelog)
values
-- 1) One-Column Classic
('one_col_classic','One-Column Classic','ATS','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience","skills","education","projects","certifications"],"default_order":["header","summary","experience","skills","education","projects","certifications"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","skills","education","projects","certifications","languages","awards","volunteering"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#1f6feb","density":"normal"}'::jsonb,
 '["pure-text","bullet-lists","no-icons"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/one_col_classic/v1/index.html',1,'Seeded base template'),

-- 2) One-Column Compact
('one_col_compact','One-Column Compact','ATS','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience","skills","education","certifications","projects"],"default_order":["header","summary","experience","skills","education","certifications","projects"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","skills","education","projects","certifications"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#0f766e","density":"compact"}'::jsonb,
 '["pure-text","high-density"]'::jsonb,
 '{"page":"A4","margins_mm":14,"min_font_pt":10}'::jsonb,
 'templates/one_col_compact/v1/index.html',1,'Seeded base template'),

-- 3) One-Column Academic CV
('one_col_academic_cv','Academic CV (One-Column)','ATS','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","education","publications","research","teaching","grants","service","awards","skills"],"default_order":["header","education","publications","research","teaching","grants","service","awards","skills"]}'::jsonb,
 '{"required":["header","education"],"optional":["publications","research","teaching","grants","service","awards","skills"]}'::jsonb,
 '{"font_head":"Georgia","font_body":"Georgia","accent":"#111827","density":"normal"}'::jsonb,
 '["long-form","enumerated-lists"]'::jsonb,
 '{"page":"Letter","margins_mm":18,"min_font_pt":11}'::jsonb,
 'templates/one_col_academic_cv/v1/index.html',1,'Seeded base template'),

-- 4) Two-Column Conservative
('two_col_conservative','Two-Column Conservative','ATS','jinja2',true,
 '{"type":"two_column","sidebar":["skills","languages","links"],"main":["header","summary","experience","education","certifications"],"default_order":["header","summary","experience","education","certifications"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","skills","languages","links","education","certifications"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#1f2937","density":"normal"}'::jsonb,
 '["sidebar","no-icons","skill-list"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/two_col_conservative/v1/index.html',1,'Seeded base template'),

-- 5) Two-Column Compact (Startup)
('two_col_compact_startup','Two-Column Compact (Startup)','ATS','jinja2',true,
 '{"type":"two_column","sidebar":["skills","links","languages"],"main":["header","summary","experience","projects","education"],"default_order":["header","summary","experience","projects","education"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","skills","links","languages","projects","education"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#2563eb","density":"compact"}'::jsonb,
 '["sidebar","high-density","project-forward"]'::jsonb,
 '{"page":"A4","margins_mm":14,"min_font_pt":10}'::jsonb,
 'templates/two_col_compact_startup/v1/index.html',1,'Seeded base template'),

-- 6) Government / Federal
('gov_federal_strict','Government / Federal (Strict)','ATS','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience","education","certifications","awards","references"],"default_order":["header","summary","experience","education","certifications","awards","references"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","education","certifications","awards","references"]}'::jsonb,
 '{"font_head":"Arial","font_body":"Arial","accent":"#000000","density":"normal"}'::jsonb,
 '["no-icons","no-color-dependence","pure-text"]'::jsonb,
 '{"page":"Letter","margins_mm":20,"min_font_pt":11}'::jsonb,
 'templates/gov_federal_strict/v1/index.html',1,'Seeded base template'),

-- 7) Two-Column Modern
('two_col_modern','Two-Column Modern','Professional','jinja2',true,
 '{"type":"two_column","sidebar":["skills","links","languages"],"main":["header","summary","experience","projects","education","certifications"],"default_order":["header","summary","experience","projects","skills","education","certifications"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","skills","links","languages","projects","education","certifications"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#1f6feb","density":"normal"}'::jsonb,
 '["sidebar","icons-optional","skill-bars-optional"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/two_col_modern/v1/index.html',1,'Seeded base template'),

-- 8) Two-Column Timeline Subtle
('two_col_timeline_subtle','Two-Column with Subtle Timeline','Professional','jinja2',true,
 '{"type":"two_column","sidebar":["skills","links"],"main":["header","summary","experience_timeline","projects","education"],"default_order":["header","summary","experience_timeline","projects","education","skills"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","projects","education","skills","links"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#0ea5e9","density":"normal"}'::jsonb,
 '["timeline-accent","sidebar"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/two_col_timeline_subtle/v1/index.html',1,'Seeded base template'),

-- 9) One-Column Header Band
('one_col_header_band','One-Column with Header Band','Professional','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header_band","summary","experience","skills","education","projects"],"default_order":["header_band","summary","experience","skills","education","projects"]}'::jsonb,
 '{"required":["header"],"optional":["summary","experience","skills","education","projects"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#334155","density":"normal"}'::jsonb,
 '["accent-band","pure-text"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/one_col_header_band/v1/index.html',1,'Seeded base template'),

-- 10) Section Boxed (Cards)
('section_boxed_cards','Section-Boxed (Cards)','Professional','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience","projects","skills","education"],"default_order":["header","summary","experience","projects","skills","education"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","projects","skills","education"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#475569","density":"normal"}'::jsonb,
 '["card-borders","subtle-shadows"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/section_boxed_cards/v1/index.html',1,'Seeded base template'),

-- 11) Left Rail Labels
('left_rail_labels','Left Rail Labels','Professional','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience","projects","education","skills"],"default_order":["header","summary","experience","projects","education","skills"],"rail":{"position":"left","width_pct":18}}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","projects","education","skills"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#1d4ed8","density":"normal"}'::jsonb,
 '["rail-labels"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/left_rail_labels/v1/index.html',1,'Seeded base template'),

-- 12) Project-Forward
('project_forward','Project-Forward','Professional','jinja2',true,
 '{"type":"two_column","sidebar":["skills","links"],"main":["header","summary","projects","experience","education"],"default_order":["header","summary","projects","experience","education","skills"]}'::jsonb,
 '{"required":["header","projects"],"optional":["summary","experience","education","skills","links"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#16a34a","density":"normal"}'::jsonb,
 '["sidebar","project-cards"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/project_forward/v1/index.html',1,'Seeded base template'),

-- 13) Visual Sidebar Tags
('visual_sidebar_tags','Visual Sidebar with Tags','Creative','jinja2',true,
 '{"type":"two_column","sidebar":["skills_tag_chips","links","languages"],"main":["header","summary","experience","projects","education"],"default_order":["header","summary","experience","projects","education"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","projects","education","skills","links","languages"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#9333ea","density":"normal"}'::jsonb,
 '["chips","icons-optional","sidebar"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/visual_sidebar_tags/v1/index.html',1,'Seeded base template'),

-- 14) Timeline Accent
('timeline_accent','Timeline Accent','Creative','jinja2',true,
 '{"type":"one_column","sidebar":[],"main":["header","summary","experience_timeline","projects","skills","education"],"default_order":["header","summary","experience_timeline","projects","skills","education"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","projects","skills","education"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#ef4444","density":"normal"}'::jsonb,
 '["timeline-accent"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/timeline_accent/v1/index.html',1,'Seeded base template'),

-- 15) Hybrid Case Studies
('hybrid_case_studies','Hybrid Resume + Mini Case Studies','Creative','jinja2',true,
 '{"type":"two_column","sidebar":["skills","links"],"main":["header","summary","experience","mini_case_studies","projects","education"],"default_order":["header","summary","mini_case_studies","experience","projects","education"]}'::jsonb,
 '{"required":["header","experience"],"optional":["summary","mini_case_studies","projects","education","skills","links"]}'::jsonb,
 '{"font_head":"Inter","font_body":"Inter","accent":"#0ea5e9","density":"normal"}'::jsonb,
 '["case-study-cards","sidebar"]'::jsonb,
 '{"page":"A4","margins_mm":16,"min_font_pt":10.5}'::jsonb,
 'templates/hybrid_case_studies/v1/index.html',1,'Seeded base template');
