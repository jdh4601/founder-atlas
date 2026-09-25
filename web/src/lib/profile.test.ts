import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadProfile } from "./profile";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("loadProfile", () => {
  it("parses the fixture profile", () => {
    const profile = loadProfile(FIXTURES_DIR);
    expect(profile.stage).toBe("pre-seed");
    expect(profile.domain).toEqual(["ai", "b2b"]);
  });

  it("throws a clear error for an invalid stage", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "profile-test-"));
    fs.writeFileSync(
      path.join(dir, "profile.yaml"),
      "stage: not-a-real-stage\ndomain: [ai]\n",
    );
    expect(() => loadProfile(dir)).toThrow(/Invalid profile/);
  });
});
