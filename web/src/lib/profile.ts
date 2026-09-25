import fs from "node:fs";
import path from "node:path";
import * as YAML from "js-yaml";
import { z } from "zod";
import { DOMAINS, STAGES, type Profile } from "./types";

const profileSchema = z.object({
  stage: z.enum(STAGES),
  domain: z.array(z.enum(DOMAINS)),
});

/** Loads and validates `profile.yaml` ("내 상황") from the content directory. */
export function loadProfile(contentDir: string): Profile {
  const filePath = path.join(contentDir, "profile.yaml");
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = YAML.load(raw);
  const result = profileSchema.safeParse(parsed);
  if (!result.success) {
    throw new Error(
      `Invalid profile.yaml at ${filePath}: ${result.error.message}`,
    );
  }
  return result.data;
}
