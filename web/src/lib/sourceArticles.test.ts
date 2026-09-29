import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadSourceArticle } from "./sourceArticles";

function writeArticle(frontmatter: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "articles-"));
  fs.mkdirSync(path.join(dir, "source_articles"));
  fs.writeFileSync(
    path.join(dir, "source_articles", "insights-001.md"),
    `---\nsource: insights-001\ntitle_ko: 제목\ntldr: 요약\nlead: 도입\n${frontmatter}source_sha256: ${"a".repeat(64)}\ngenerated_at: '2026-09-28'\n---\n## 1. 본문\n\n- 항목\n`,
  );
  return dir;
}

it("reads optional topic tags from an article", () => {
  const article = loadSourceArticle(writeArticle("tags:\n- 채용\n- 가격\n"), "insights-001");
  expect(article?.tags).toEqual(["채용", "가격"]);
});

it("defaults to no tags", () => {
  expect(loadSourceArticle(writeArticle(""), "insights-001")?.tags).toEqual([]);
});
