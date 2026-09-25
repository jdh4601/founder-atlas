import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadRepoRootEnvFrom } from "./env";

describe("loadRepoRootEnvFrom", () => {
  const originalEnv = { ...process.env };
  let dir: string;

  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "env-test-"));
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("loads KEY=VALUE lines from the given .env file into process.env", () => {
    fs.writeFileSync(
      path.join(dir, ".env"),
      "ANTHROPIC_API_KEY=sk-test-123\nOTHER=value\n",
    );
    delete process.env.ANTHROPIC_API_KEY;
    delete process.env.OTHER;

    loadRepoRootEnvFrom(path.join(dir, ".env"));

    expect(process.env.ANTHROPIC_API_KEY).toBe("sk-test-123");
    expect(process.env.OTHER).toBe("value");
  });

  it("strips matching single or double quotes around the value", () => {
    fs.writeFileSync(
      path.join(dir, ".env"),
      'A="double"\nB=\'single\'\n',
    );
    delete process.env.A;
    delete process.env.B;

    loadRepoRootEnvFrom(path.join(dir, ".env"));

    expect(process.env.A).toBe("double");
    expect(process.env.B).toBe("single");
  });

  it("never overrides a variable already set in process.env", () => {
    fs.writeFileSync(path.join(dir, ".env"), "ANTHROPIC_API_KEY=from-file\n");
    process.env.ANTHROPIC_API_KEY = "from-shell";

    loadRepoRootEnvFrom(path.join(dir, ".env"));

    expect(process.env.ANTHROPIC_API_KEY).toBe("from-shell");
  });

  it("does nothing (no throw) when the file does not exist", () => {
    expect(() =>
      loadRepoRootEnvFrom(path.join(dir, "does-not-exist.env")),
    ).not.toThrow();
  });

  it("ignores comments and blank lines", () => {
    fs.writeFileSync(
      path.join(dir, ".env"),
      "# a comment\n\nFOO=bar\n",
    );
    delete process.env.FOO;

    loadRepoRootEnvFrom(path.join(dir, ".env"));

    expect(process.env.FOO).toBe("bar");
  });
});
