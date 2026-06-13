// Simulated DFT dispatch — atomate2 workflows on SLURM@perlmutter with
// custodian auto-handling SCF / convergence failures. (Faithful simulation;
// no real HPC backend in this build.)
export type JobStatus = "converged" | "running" | "queued" | "flagged" | "failed";

export interface Job {
  id: string;
  f: string; // formula
  calc: string;
  func: string;
  k: string; // k-mesh
  st: JobStatus;
  prog: number;
  scf: string;
  de: string;
  wall: string;
  warn?: string;
}

export const JOBS: Job[] = [
  { id: "tk-7741", f: "HfO₂", calc: "relax", func: "r²SCAN", k: "Γ 8×8×8", st: "converged", prog: 100, scf: "38", de: "8e-7", wall: "1h12m" },
  { id: "tk-7742", f: "ZrO₂", calc: "relax", func: "r²SCAN", k: "8×8×8", st: "converged", prog: 100, scf: "31", de: "6e-7", wall: "1h04m" },
  { id: "tk-7748", f: "La₂O₃", calc: "relax", func: "r²SCAN", k: "6×6×4", st: "running", prog: 64, scf: "—", de: "—", wall: "0h41m", warn: "SCF oscillation → custodian: ALGO=All, AMIX=0.1" },
  { id: "tk-7751", f: "HfO₂", calc: "dielectric DFPT", func: "PBE", k: "6×6×6", st: "running", prog: 88, scf: "—", de: "—", wall: "2h18m" },
  { id: "tk-7755", f: "HfO₂", calc: "band gap", func: "HSE06", k: "4×4×4", st: "queued", prog: 0, scf: "—", de: "—", wall: "—", warn: "PBE gap 4.05 eV underestimate → HSE06 for top 3" },
  { id: "tk-7758", f: "TiO₂", calc: "relax", func: "r²SCAN", k: "8×8×8", st: "converged", prog: 100, scf: "27", de: "9e-7", wall: "0h48m" },
  { id: "tk-7760", f: "SrTiO₃", calc: "static", func: "PBE+U", k: "8×8×8", st: "flagged", prog: 100, scf: "44", de: "3e-6", wall: "0h36m", warn: "pruned-grid risk → PREC=Accurate; e_hull recheck" },
  { id: "tk-7763", f: "Ta₂O₅", calc: "relax", func: "r²SCAN", k: "4×6×4", st: "failed", prog: 0, scf: "200", de: "1e-3", wall: "3h02m", warn: "custodian: not converged in 200 ionic steps → requeue NELM=250" },
  { id: "tk-7767", f: "Al₂O₃", calc: "dielectric DFPT", func: "PBE", k: "6×6×6", st: "running", prog: 52, scf: "—", de: "—", wall: "1h28m" },
  { id: "tk-7770", f: "HfSiO₄", calc: "relax", func: "r²SCAN", k: "6×6×6", st: "queued", prog: 0, scf: "—", de: "—", wall: "—" },
  { id: "tk-7772", f: "Y₂O₃", calc: "relax", func: "r²SCAN", k: "4×4×4", st: "converged", prog: 100, scf: "35", de: "7e-7", wall: "0h52m" },
];

export const JOB_STATUS_STYLE: Record<JobStatus, { c: string; bg: string; br: string }> = {
  converged: { c: "var(--color-ok)", bg: "var(--color-ok-tint)", br: "var(--color-ok-border)" },
  running: { c: "var(--color-amber-deep)", bg: "var(--color-amber-tint)", br: "var(--color-amber-border)" },
  queued: { c: "var(--color-muted)", bg: "var(--color-panel)", br: "var(--color-hair)" },
  flagged: { c: "var(--color-warn)", bg: "var(--color-amber-tint)", br: "var(--color-amber-border)" },
  failed: { c: "var(--color-danger)", bg: "var(--color-danger-tint)", br: "var(--color-danger-border)" },
};
