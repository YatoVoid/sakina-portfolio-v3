/**
 * V3 content.js — All project data, skills, and bio copy.
 * This is the single source of truth for portfolio content.
 * Populate from portfolio.ts when copying assets from V2.
 *
 * VHS tape ↔ project mapping:
 *   Slot 0 — DENTAL-X  → Dental radiograph AI project
 *   Slot 1 — HOUSING AI → CanIOwnAHome / Houston housing
 *   Slot 2 — FLOOD CAST → FloodCast hotspot prediction
 *   Slot 3 — POWERGUARD → PowerGuard 360
 *   Slot 4 — WARMTHREAD → WarmThread / Axintel
 *   Slot 5 — SUMUS      → SUMUS consulting dashboard
 *   Slot 6 — RESUME     → Opens resume PDF
 */

const CONTENT = {
  // ── Personal bio ─────────────────────────────────────────────────────────
  name:     'Sakina Saifuddin',
  title:    'Data Scientist & ML Engineer',
  location: 'Houston, TX',
  email:    'sakinasaifee875@gmail.com',
  github:   'https://github.com/sakina-saifuddin',
  linkedin: 'https://www.linkedin.com/in/sakina-saifuddin',
  resume:   './assets/resume/sakina-saifuddin-resume.pdf',

  // ── Project entries ───────────────────────────────────────────────────────
  projects: [
    {
      id:          'dental-x',
      tapeSlot:    0,
      title:       'DentalX AI',
      category:    'COMPUTER VISION',
      description: 'Deep-learning pipeline for detecting dental anomalies in periapical radiographs. ' +
                   'Fine-tuned YOLOv8 on a curated dataset of 3,200 annotated X-rays, achieving 91 % mAP. ' +
                   'Built a FastAPI inference service containerised in Docker.',
      tech:        ['Python', 'YOLOv8', 'FastAPI', 'Docker', 'DICOM'],
      github:      '',
      demo:        '',
      year:        '2025',
    },
    {
      id:          'housing-ai',
      tapeSlot:    1,
      title:       'Can I Own a Home?',
      category:    'DATA SCIENCE / WEB',
      description: 'Interactive affordability tool for the Houston metro area. ' +
                   'Combines live MLS data, income percentiles, and FHA/conventional mortgage calculators ' +
                   'to tell users whether home ownership is reachable this year. ' +
                   'Deployed on Netlify with serverless price-feed updates.',
      tech:        ['Python', 'pandas', 'Netlify', 'JavaScript', 'Housing APIs'],
      github:      'https://github.com/YatoVoid/CanIOwnAHome',
      demo:        'https://canownhome.netlify.app',
      year:        '2026',
    },
    {
      id:          'flood-cast',
      tapeSlot:    2,
      title:       'FloodCast',
      category:    'ML / GEOSPATIAL',
      description: 'Spatio-temporal model for predicting Houston flood hotspots 24 h ahead. ' +
                   'Fuses LIDAR elevation, imperviousness, rainfall radar, and historical FEMA claims. ' +
                   'Course project for COSC 6368 (AI). ' +
                   'Gradient-boosted ensemble + probabilistic map output.',
      tech:        ['Python', 'XGBoost', 'GeoPandas', 'GDAL', 'H3', 'Folium'],
      github:      'https://github.com/sakina-saifuddin/Spatio-Temporal-Urban-Flood-Hotspot-Prediction-with-Multi-Source-Geospatial-Data-Engineering-',
      demo:        '',
      year:        '2026',
    },
    {
      id:          'powerguard',
      tapeSlot:    3,
      title:       'PowerGuard 360',
      category:    'AI AGENT / ENERGY',
      description: 'AI-driven grid-resilience platform for energy distribution networks. ' +
                   'Won Best Pitch & Demo at CodeRED Orion hackathon (Chevron sponsor track). ' +
                   'Combines anomaly detection on SCADA data with an LLM agent for incident triage.',
      tech:        ['Python', 'LangChain', 'Streamlit', 'Time-series ML', 'SCADA'],
      github:      '',
      demo:        '',
      year:        '2026',
    },
    {
      id:          'warmthread',
      tapeSlot:    4,
      title:       'WarmThread — Axintel',
      category:    'ML PIPELINE',
      description: 'Junior Data Scientist engagement at WarmThread (Axintel). ' +
                   'Built ML pipeline on de-identified behavioral-health call transcripts: ' +
                   'NLP preprocessing, multi-label intent classification, and outcome-risk scoring. ' +
                   'Deployed on internal REST API consumed by care-coordinator dashboard.',
      tech:        ['Python', 'HuggingFace', 'scikit-learn', 'FastAPI', 'NLP'],
      github:      '',
      demo:        '',
      year:        '2026',
    },
    {
      id:          'sumus',
      tapeSlot:    5,
      title:       'SUMUS Analytics',
      category:    'DATA ANALYTICS',
      description: 'Consulting engagement for SUMUS. ' +
                   'Delivered marketing analytics dashboard covering campaign performance, ' +
                   'audience segmentation, and funnel attribution across paid channels.',
      tech:        ['Python', 'Power BI', 'SQL', 'GA4', 'Meta Ads API'],
      github:      '',
      demo:        '',
      year:        '2026',
    },
    {
      id:          'resume',
      tapeSlot:    6,
      title:       'Resume',
      category:    'DOCUMENT',
      description: 'Full CV including education, work experience, publications, and projects.',
      tech:        [],
      github:      '',
      demo:        '', // filled at runtime from CONTENT.resume
      year:        '2026',
    },
  ],

  // ── Skills ────────────────────────────────────────────────────────────────
  skills: {
    languages:  ['Python', 'SQL', 'JavaScript', 'R', 'Bash'],
    ml:         ['PyTorch', 'TensorFlow', 'HuggingFace', 'scikit-learn', 'XGBoost', 'LangChain'],
    data:       ['pandas', 'NumPy', 'Spark', 'dbt', 'Airflow', 'GeoPandas'],
    infra:      ['Docker', 'FastAPI', 'AWS (S3, Lambda, SageMaker)', 'GCP BigQuery', 'Netlify'],
    viz:        ['Tableau', 'Power BI', 'Plotly', 'D3.js', 'Three.js'],
    tools:      ['Git', 'Jupyter', 'VS Code', 'Blender', 'Figma'],
  },

  // ── Education ─────────────────────────────────────────────────────────────
  education: [
    {
      school:  'University of Houston',
      degree:  'M.S. Computer Science — AI/ML concentration',
      period:  '2025 – 2027',
    },
    {
      school:  'NED University of Engineering & Technology',
      degree:  'B.E. Computer Science',
      period:  '2018 – 2022',
    },
  ],
};

// Runtime fix: set resume demo URL
CONTENT.projects.find(p => p.id === 'resume').demo = CONTENT.resume;
