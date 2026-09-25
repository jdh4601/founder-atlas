import path from "node:path";
import { getContentDir } from "./contentDir";

describe("getContentDir", () => {
  const originalEnv = process.env.CONTENT_DIR;

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.CONTENT_DIR;
    } else {
      process.env.CONTENT_DIR = originalEnv;
    }
  });

  it("defaults to ../content relative to the working directory", () => {
    delete process.env.CONTENT_DIR;
    expect(getContentDir()).toBe(path.resolve(process.cwd(), "../content"));
  });

  it("uses CONTENT_DIR when set, resolved relative to the working directory", () => {
    process.env.CONTENT_DIR = "./__fixtures__/content";
    expect(getContentDir()).toBe(
      path.resolve(process.cwd(), "./__fixtures__/content"),
    );
  });

  it("passes through an absolute CONTENT_DIR unchanged", () => {
    process.env.CONTENT_DIR = "/tmp/some-content";
    expect(getContentDir()).toBe("/tmp/some-content");
  });
});
