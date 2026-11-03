// What the notebook says. Only the TODO heading is on the page when the scene loads. Picking up the pencil writes its items, turns the page and writes page 2.
// A page holds 10 ruled lines. The heading takes 2, and a long item wraps onto a second line.
export const NOTEBOOK_PAGES = [
  {
    heading: "TODO",
    circle: true,
    items: [
      "post what I learned every week",
      "sign up for the next hackathon",
      "send 10 applications a week",
      "finish one ML project end to end",
      "10 LeetCode and SQL questions a week",
      "earn a cert: Claude Code, NVIDIA or Google"
    ]
  },
  {
    heading: "Goals for 2027",
    circle: false,
    items: [
      "graduate with my masters",
      "start full time as an AI engineer",
      "lead a team to a hackathon win",
      "publish a paper or preprint",
      "get fit and run a 5K",
      "travel somewhere new",
      "be known for one thing in AI",
      "go to GTC, CVPR and NeurIPS"
    ]
  }
];
