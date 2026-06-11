import * as fs from 'fs';
import * as path from 'path';

export interface EvidenceContext {
  env: string;
  portal: string;
  module: string;
  feature: string;
}

export function evidenceDir(ctx: EvidenceContext, tcId: string): string {
  return path.join(process.cwd(), 'evidence', ctx.env, ctx.portal, ctx.module, ctx.feature, tcId);
}

export function ev(ctx: EvidenceContext, tcId: string): (step: string) => string {
  const dir = evidenceDir(ctx, tcId);
  fs.mkdirSync(dir, { recursive: true });
  return (step: string) => path.join(dir, `${step}.png`);
}
