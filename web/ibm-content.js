export const BOOT = [
  "Sakina Computer BASIC Version 3.0",
  "Copyright (C) 1984, Sakina Saifuddin",
  "61440 Bytes free",
  "",
  "Hi! Type ABOUT to start, or HELP."
];

export const BAR = [
  {key: "1", label: "ABOUT", cmd: "ABOUT"},
  {key: "2", label: "WORK", cmd: "WORK"},
  {key: "3", label: "PROJECTS", cmd: "PROJECTS"},
  {key: "4", label: "HACKS", cmd: "HACKS"},
  {key: "5", label: "CONTACT", cmd: "CONTACT"}
];

const about = [
  "Hi, I'm Sakina Saifuddin.",
  "Software engineer and data scientist in Houston, Texas, with 3.5+ years across software, data, automation and machine learning.",
  "",
  "I started in code. In 2021 I began a computer science degree at Iqra University in Karachi and, the same year, started building real apps at SoftSyncDev with React Native, Node.js and AWS. One early win: a fitness app whose videos took about five minutes to load now loads them in about three seconds.",
  "",
  "In 2022 I took a second job reading data about people. At The Walnut Agency I managed 70+ client accounts and used campaign data to grow engagement by 60%+. That is where numbers started to explain behavior for me.",
  "",
  "I wanted to work with the data itself, so I moved into business intelligence. At BluTech Consulting I built Power BI and Tableau dashboards on SQL for a major bank. My dashboards and SQL now sit behind 1,074 automated reports.",
  "",
  "Then machine learning. A research project on classifying seizures from EEG data pulled me in, and in 2025 I started a Master's in Engineering Data Science and AI at the University of Houston.",
  "",
  "I am not a healthcare-only candidate. I have trained EEG classifiers, chest X-ray GANs and healthcare data pipelines. I have also forecast retail demand over 3 million records, built finance pipelines, shipped mobile apps and run marketing analytics. I do all of it.",
  "",
  "Hackathons are my second passion. At CodeRED Orion, the University of Houston's biggest hackathon, I led our team to 2nd place out of 70+ teams and the Best Pitch/Demo award with Power Guard 360. I keep signing up for more.",
  "",
  "I am also lazy, on purpose. If I hate doing something by hand, I automate it. I automated my own job search: Sakina Job OS is a 12-stage agent that finds postings, checks fit, writes my resume and cover letter, finds warm LinkedIn contacts and drafts follow-ups. A human review step stops anything going out without me.",
  "",
  "My aim: become an AI engineer who builds automation, the agents and pipelines that remove the manual work people hate doing.",
  "",
  "Type ROLES to see what I am looking for."
];

const roles = [
  "I am looking for early-career roles, internships and co-ops as:",
  "",
  "  AI Engineer",
  "  AI Automation Engineer",
  "  Machine Learning Engineer",
  "  Data Scientist",
  "",
  "Healthcare, finance, retail, marketing. The domain matters less to me than the problem: something slow, manual or repetitive that a good system can take over.",
  "",
  "Based in Houston, Texas."
];

const work = [
  "5 roles so far:",
  "",
  "Feb 2026 - Present",
  "  BI & Automation Intern, TMAC / NIST-MEP",
  "May 2026 - Sep 2026",
  "  AI Automation Engineer, Dental-X AI",
  "May 2024 - Aug 2025",
  "  Business Intelligence Consultant, BluTech Consulting",
  "Aug 2022 - Sep 2025",
  "  Sr. Performance Management Analyst, The Walnut Agency",
  "Jan 2021 - May 2024",
  "  Software Engineer, SoftSyncDev",
  "",
  "Education: MS Engineering Data Science and AI, University of Houston (2025 - now). BS Computer Science, Iqra University (GPA 3.71, Gold Medalist)."
];

const projects = [
  "11 project books at askksakina.netlify.app. The big ones:",
  "",
  "1  Power Guard 360. Predicts power plant turbine failures. 2nd place at CodeRED Orion.",
  "2  Sakina Job OS. 12-stage n8n agent that runs my job search.",
  "3  Retail Forecasting. 3M+ records, LightGBM beat two other models.",
  "4  Grant Dashboards. Power BI plus Databricks, a two-day prep step automated.",
  "5  Oracle Financial ETL. Python pipeline from Oracle exports to Power BI.",
  "6  Pneumonia X-ray GAN. Accuracy from 73.56% to 82.21%.",
  "7  EEG Seizure Detection. Deep learning on brain signals.",
  "8  Healthcare Eligibility Pipeline. Many payers, one benefit summary.",
  "9  Cost Center App. Monthly sign-off in Power Apps and SharePoint.",
  "10 Fitness Video Fix. Five minutes down to about three seconds."
];

const hacks = [
  "Hackathons are my second passion.",
  "",
  "CodeRED Orion, University of Houston, 70+ teams.",
  "I led our team to 2nd place and the Best Pitch/Demo award ($500) with Power Guard 360.",
  "",
  "Two Random Forest models watch every turbine's sensor data and flag failures with the reasons behind them. A live Arduino sensor board drives one turbine and watches for gas leaks, a 3D digital twin shows the whole plant, and the engineer's phone app takes them to the job.",
  "",
  "Fast build, clear story, working demo. That is the part I enjoy."
];

const contact = [
  "Open to internships, co-ops and early-career roles.",
  "",
  "Email     sakinasaifee006@gmail.com",
  "LinkedIn  linkedin.com/in/sakinasaifuddin",
  "GitHub    github.com/sakina-saifuddin",
  "Ask me    askksakina.netlify.app",
  "",
  "Type EMAIL, LINKEDIN, GITHUB or ASK to open one."
];

const help = [
  "Commands:",
  "  ABOUT     my story",
  "  ROLES     what I am looking for",
  "  WORK      where I have worked",
  "  PROJECTS  what I have built",
  "  HACKS     hackathons",
  "  CONTACT   how to reach me",
  "  CLEAR     clear the screen"
];

export const commands = {
  ABOUT: {lines: about},
  ROLES: {lines: roles},
  AIM: {lines: roles},
  WORK: {lines: work},
  EXPERIENCE: {lines: work},
  PROJECTS: {lines: projects},
  HACKS: {lines: hacks},
  HACKATHONS: {lines: hacks},
  CONTACT: {lines: contact},
  HELP: {lines: help},
  EMAIL: {href: "mailto:sakinasaifee006@gmail.com", lines: ["Opening your mail app."]},
  LINKEDIN: {href: "https://www.linkedin.com/in/sakinasaifuddin/", lines: ["Opening LinkedIn in a new tab."]},
  GITHUB: {href: "https://github.com/sakina-saifuddin", lines: ["Opening GitHub in a new tab."]},
  ASK: {href: "https://askksakina.netlify.app", lines: ["Opening AskSakina in a new tab."]}
};
