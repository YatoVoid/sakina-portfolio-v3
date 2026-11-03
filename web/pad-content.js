import {projects} from "./content.js";

const titles = projects.map(p => p.title);

export const pad = {
  title: "Work",
  sections: [
    { head: "Experiences", items: titles.slice(0, 6) },
    { head: "Projects", items: titles.slice(6) }
  ]
};
