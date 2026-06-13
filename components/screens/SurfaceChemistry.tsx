"use client";

import * as THREE from "three";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { SURFACE_SYSTEMS } from "@/lib/data/surface";

const smooth = (x: number, a: number, b: number) => {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const energyOf = (xi: number, m: { dE: number; Ea: number }) =>
  m.dE * smooth(xi, 0.48, 0.95) + m.Ea * Math.exp(-Math.pow((xi - 0.5) / 0.15, 2));

interface Engine {
  tau: number;
  playing: boolean;
  mat: number;
  dragging: boolean;
  spin: boolean;
  renderer?: THREE.WebGLRenderer;
  scene?: THREE.Scene;
  camera?: THREE.PerspectiveCamera;
  world?: THREE.Group;
  alMesh?: THREE.Mesh;
  surfH?: THREE.Mesh;
  m1?: THREE.Group;
  m2?: THREE.Group;
  m3?: THREE.Group;
  bonds?: Record<string, THREE.Mesh>;
  raf?: number;
  cleanup?: () => void;
}

export function SurfaceChemistry() {
  const router = useRouter();
  const [mat, setMat] = useState(1);
  const [playing, setPlaying] = useState(false);
  const [escalated, setEscalated] = useState(false);
  const [tauPct, setTauPct] = useState(0);

  const glHost = useRef<HTMLDivElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const slider = useRef<HTMLInputElement>(null);
  const stageLabel = useRef<HTMLElement>(null);
  const bondLabel = useRef<HTMLElement>(null);
  const dot = useRef<SVGCircleElement>(null);
  const curE = useRef<HTMLElement>(null);
  const fallback = useRef<HTMLDivElement>(null);
  const eng = useRef<Engine>({ tau: 0, playing: false, mat: 1, dragging: false, spin: true });

  const m = SURFACE_SYSTEMS[mat];

  // keep engine in sync with React state
  useEffect(() => {
    eng.current.playing = playing;
  }, [playing]);
  useEffect(() => {
    eng.current.mat = mat;
    const e = eng.current;
    if (e.alMesh) {
      const s = SURFACE_SYSTEMS[mat];
      (e.alMesh.material as THREE.MeshPhongMaterial).color.set(parseInt(s.color.slice(1), 16));
      e.alMesh.scale.setScalar(s.mr);
    }
  }, [mat]);

  // mount Three.js scene once
  useEffect(() => {
    const host = glHost.current;
    const st = stage.current;
    if (!host || !st) return;

    const e = eng.current;
    const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
    const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
    const lerpV = (p: THREE.Vector3, q: THREE.Vector3, t: number) =>
      V(lerp(p.x, q.x, t), lerp(p.y, q.y, t), lerp(p.z, q.z, t));
    const YUP = V(0, 1, 0);

    const C_O = 0xb23b2e,
      C_H = 0xdcdad2,
      C_C = 0x34332f,
      C_M = 0x7c92a6,
      C_BOND = 0xb0ada4,
      C_AMBER = 0xb45309;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      if (fallback.current) fallback.current.style.display = "flex";
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    const sz = () => ({ w: host.clientWidth || 700, h: host.clientHeight || 452 });
    const s = sz();
    renderer.setSize(s.w, s.h);
    host.appendChild(renderer.domElement);
    e.renderer = renderer;

    const scene = new THREE.Scene();
    e.scene = scene;
    const cam = new THREE.PerspectiveCamera(42, s.w / s.h, 0.1, 100);
    cam.position.set(0, 2.6, 9.4);
    cam.lookAt(0, 1.25, 0);
    e.camera = cam;
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const d1 = new THREE.DirectionalLight(0xffffff, 0.72);
    d1.position.set(5, 8, 6);
    scene.add(d1);
    const d2 = new THREE.DirectionalLight(0xffffff, 0.26);
    d2.position.set(-4, 3, -5);
    scene.add(d2);
    const world = new THREE.Group();
    world.rotation.x = 0.24;
    scene.add(world);
    e.world = world;

    const sg = new THREE.SphereGeometry(1, 26, 26);
    const cg = new THREE.CylinderGeometry(1, 1, 1, 14);
    const atom = (par: THREE.Object3D, r: number, col: number, op: number, pos?: THREE.Vector3) => {
      const mt = new THREE.MeshPhongMaterial({ color: col, shininess: 42, specular: 0x2a2a2a, transparent: op < 1, opacity: op });
      const me = new THREE.Mesh(sg, mt);
      me.scale.setScalar(r);
      if (pos) me.position.copy(pos);
      par.add(me);
      return me;
    };
    const sBond = (par: THREE.Object3D, p: THREE.Vector3, q: THREE.Vector3, r: number, col: number, op: number) => {
      const mt = new THREE.MeshPhongMaterial({ color: col, shininess: 30, transparent: op < 1, opacity: op });
      const c = new THREE.Mesh(cg, mt);
      const dir = q.clone().sub(p);
      c.position.copy(p).add(q).multiplyScalar(0.5);
      c.scale.set(r, dir.length(), r);
      c.quaternion.setFromUnitVectors(YUP, dir.clone().normalize());
      par.add(c);
      return c;
    };
    const dBond = (r: number, col: number) => {
      const mt = new THREE.MeshPhongMaterial({ color: col, shininess: 30, transparent: true, opacity: 1 });
      const c = new THREE.Mesh(cg, mt);
      c.userData.r = r;
      world.add(c);
      return c;
    };

    // surface lattice
    const O0 = V(0, 0, 0);
    [[-1.6, 0, -1.6], [-1.6, 0, 0], [-1.6, 0, 1.6], [0, 0, -1.6], [0, 0, 1.6], [1.6, 0, -1.6], [1.6, 0, 0], [1.6, 0, 1.6]].forEach((p) =>
      atom(world, 0.4, C_O, 0.55, V(p[0], p[1], p[2])),
    );
    [[-0.8, -1, -0.8], [-0.8, -1, 0.8], [0.8, -1, -0.8], [0.8, -1, 0.8], [-2.4, -1.05, 0], [2.4, -1.05, 0], [0, -1.05, -2.4], [0, -1.05, 2.4]].forEach((p, i) =>
      atom(world, i < 4 ? 0.52 : 0.44, C_M, i < 4 ? 0.62 : 0.42, V(p[0], p[1], p[2])),
    );
    [[-0.8, -1, -0.8], [-0.8, -1, 0.8], [0.8, -1, -0.8], [0.8, -1, 0.8]].forEach((p) =>
      sBond(world, O0, V(p[0], p[1], p[2]), 0.085, C_BOND, 0.45),
    );
    atom(world, 0.46, C_O, 1, O0);
    e.surfH = atom(world, 0.32, C_H, 1, V(0, 0.98, 0));
    const cur = SURFACE_SYSTEMS[eng.current.mat];
    e.alMesh = atom(world, cur.mr, parseInt(cur.color.slice(1), 16), 1, V(0, 3.2, 0.2));

    const methyl = () => {
      const g = new THREE.Group();
      atom(g, 0.45, C_C, 1, V(0, 0, 0));
      for (let k = 0; k < 3; k++) {
        const a = (k * 2 * Math.PI) / 3;
        const hp = V(0.94 * Math.cos(a), -0.34, 0.94 * Math.sin(a));
        atom(g, 0.32, C_H, 1, hp);
        sBond(g, V(0, 0, 0), hp, 0.075, C_BOND, 1);
      }
      world.add(g);
      return g;
    };
    e.m1 = methyl();
    e.m2 = methyl();
    e.m3 = methyl();
    e.bonds = {
      AlC1: dBond(0.1, C_BOND),
      AlC2: dBond(0.1, C_BOND),
      AlC3: dBond(0.1, C_BOND),
      AlO: dBond(0.13, C_AMBER),
      OH: dBond(0.09, C_BOND),
      C1H: dBond(0.09, C_BOND),
    };

    const upd = (c: THREE.Mesh, p: THREE.Vector3, q: THREE.Vector3, op: number) => {
      if (op < 0.025) {
        c.visible = false;
        return;
      }
      c.visible = true;
      const dir = q.clone().sub(p);
      const len = dir.length();
      if (len < 1e-4) {
        c.visible = false;
        return;
      }
      c.position.copy(p).add(q).multiplyScalar(0.5);
      c.scale.set(c.userData.r, len, c.userData.r);
      c.quaternion.setFromUnitVectors(YUP, dir.clone().normalize());
      (c.material as THREE.MeshPhongMaterial).opacity = op;
    };

    const frameGL = (tau: number) => {
      const al = e.alMesh!,
        b = e.bonds!;
      const AL0 = V(0, 3.2, 0.2),
        AL1 = V(0, 1.95, 0),
        OH0 = V(0, 0.98, 0);
      const M1_0 = V(0.15, 2.15, 1.25),
        M1_1 = V(0.55, 4.55, 1.95),
        M2_0 = V(-1.15, 2.15, -0.75),
        M2_1 = V(-1.5, 2.72, -0.7),
        M3_0 = V(1.25, 2.15, -0.6),
        M3_1 = V(1.5, 2.72, -0.7);
      al.position.copy(lerpV(AL0, AL1, smooth(tau, 0.1, 0.6)));
      e.m2!.position.copy(lerpV(M2_0, M2_1, smooth(tau, 0.15, 0.85)));
      e.m3!.position.copy(lerpV(M3_0, M3_1, smooth(tau, 0.15, 0.85)));
      const base = lerpV(M1_0, M1_1, smooth(tau, 0.3, 0.95));
      const drift = Math.pow(Math.max(0, (tau - 0.6) / 0.4), 1.6) * 3.2;
      e.m1!.position.set(base.x, base.y + drift, base.z + drift * 0.25);
      const dock = e.m1!.position.clone().add(V(0, 1, 0));
      e.surfH!.position.copy(lerpV(OH0, dock, smooth(tau, 0.45, 0.86)));
      const aim = (g: THREE.Object3D, t: THREE.Vector3) => {
        const d = t.clone().sub(g.position);
        if (d.lengthSq() > 1e-6) g.quaternion.setFromUnitVectors(YUP, d.normalize());
      };
      aim(e.m2!, al.position);
      aim(e.m3!, al.position);
      const dirAl = al.position.clone().sub(e.m1!.position).normalize();
      const w1 = smooth(tau, 0.4, 0.78);
      const dM1 = dirAl.multiplyScalar(1 - w1).add(YUP.clone().multiplyScalar(w1));
      if (dM1.lengthSq() > 1e-6) e.m1!.quaternion.setFromUnitVectors(YUP, dM1.normalize());
      upd(b.AlC1, al.position, e.m1!.position, 1 - smooth(tau, 0.4, 0.6));
      upd(b.AlC2, al.position, e.m2!.position, 1);
      upd(b.AlC3, al.position, e.m3!.position, 1);
      upd(b.AlO, al.position, O0, smooth(tau, 0.45, 0.68));
      upd(b.OH, O0, e.surfH!.position, 1 - smooth(tau, 0.4, 0.56));
      upd(b.C1H, e.m1!.position, e.surfH!.position, smooth(tau, 0.52, 0.82));
    };

    const updateHUD = (tau: number) => {
      const sys = SURFACE_SYSTEMS[eng.current.mat];
      if (slider.current && !eng.current.dragging) slider.current.value = String(tau * 1000);
      if (stageLabel.current)
        stageLabel.current.textContent = tau < 0.4 ? "APPROACH" : tau < 0.66 ? "TRANSITION" : "RELEASE · " + sys.by;
      if (bondLabel.current) {
        const f = tau >= 0.7;
        bondLabel.current.textContent = f ? "formed ✓" : "forming…";
        bondLabel.current.style.color = f ? "var(--color-ok)" : "var(--color-muted)";
      }
      const E = energyOf(tau, sys);
      const Emax = sys.Ea + 0.2,
        Emin = Math.min(sys.dE, 0) - 0.2;
      const cx = 38 + tau * 268,
        cy = 14 + ((Emax - E) / (Emax - Emin)) * 150;
      if (dot.current) {
        dot.current.setAttribute("cx", cx.toFixed(1));
        dot.current.setAttribute("cy", cy.toFixed(1));
      }
      if (curE.current) curE.current.textContent = E.toFixed(2);
    };

    const clock = new THREE.Clock();
    let lastPct = -1;
    const loop = () => {
      e.raf = requestAnimationFrame(loop);
      const dt = clock.getDelta();
      if (e.playing) {
        e.tau += dt * 0.26;
        if (e.tau >= 1) {
          e.tau = 1;
          setPlaying(false);
        }
      }
      if (e.spin && !e.dragging && e.world) e.world.rotation.y += 0.0024;
      frameGL(e.tau);
      updateHUD(e.tau);
      const pct = Math.round(e.tau * 100);
      if (pct !== lastPct) {
        lastPct = pct;
        setTauPct(pct);
      }
      if (e.renderer) e.renderer.render(e.scene!, e.camera!);
    };
    loop();

    // interaction
    const onResize = () => {
      const z = sz();
      cam.aspect = z.w / z.h;
      cam.updateProjectionMatrix();
      renderer.setSize(z.w, z.h);
    };
    window.addEventListener("resize", onResize);
    let px = 0,
      py = 0;
    const down = (ev: PointerEvent) => {
      e.dragging = true;
      px = ev.clientX;
      py = ev.clientY;
      st.style.cursor = "grabbing";
      try {
        st.setPointerCapture(ev.pointerId);
      } catch {}
    };
    const move = (ev: PointerEvent) => {
      if (!e.dragging) return;
      const dx = ev.clientX - px,
        dy = ev.clientY - py;
      px = ev.clientX;
      py = ev.clientY;
      world.rotation.y += dx * 0.008;
      world.rotation.x = clamp(world.rotation.x + dy * 0.008, -0.85, 1.0);
    };
    const up = () => {
      e.dragging = false;
      st.style.cursor = "grab";
    };
    const wheel = (ev: WheelEvent) => {
      ev.preventDefault();
      cam.position.z = clamp(cam.position.z + ev.deltaY * 0.01, 5, 16);
    };
    st.addEventListener("pointerdown", down);
    st.addEventListener("pointermove", move);
    st.addEventListener("pointerup", up);
    st.addEventListener("pointerleave", up);
    st.addEventListener("wheel", wheel, { passive: false });

    e.cleanup = () => {
      cancelAnimationFrame(e.raf!);
      window.clearTimeout((e as Engine & { sb?: number }).sb);
      window.removeEventListener("resize", onResize);
      st.removeEventListener("pointerdown", down);
      st.removeEventListener("pointermove", move);
      st.removeEventListener("pointerup", up);
      st.removeEventListener("pointerleave", up);
      st.removeEventListener("wheel", wheel);
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
    };
    return () => e.cleanup?.();
  }, []);

  // energy curve geometry (re-rendered per material)
  const Emax = m.Ea + 0.2,
    Emin = Math.min(m.dE, 0) - 0.2;
  const pxi = (xi: number) => 38 + xi * 268;
  const pyE = (E: number) => 14 + ((Emax - E) / (Emax - Emin)) * 150;
  let curveD = "";
  for (let xi = 0; xi <= 1.0001; xi += 0.025) curveD += (curveD ? "L" : "M") + pxi(xi).toFixed(1) + " " + pyE(energyOf(xi, m)).toFixed(1) + " ";

  const onPlay = () => {
    if (eng.current.tau >= 1) eng.current.tau = 0;
    setPlaying((p) => !p);
  };
  const onScrub = (ev: React.FormEvent<HTMLInputElement>) => {
    eng.current.tau = +(ev.target as HTMLInputElement).value / 1000;
    eng.current.dragging = true;
    setPlaying(false);
    window.clearTimeout((eng.current as Engine & { sb?: number }).sb);
    (eng.current as Engine & { sb?: number }).sb = window.setTimeout(() => {
      eng.current.dragging = false;
    }, 250);
  };
  const onReset = () => {
    if (eng.current.world) eng.current.world.rotation.set(0.24, 0, 0);
    if (eng.current.camera) {
      eng.current.camera.position.set(0, 2.6, 9.4);
      eng.current.camera.lookAt(0, 1.25, 0);
    }
  };

  return (
    <div className="p-5">
      <div className="mx-auto max-w-[1040px] overflow-hidden rounded-[4px] border border-line bg-surface shadow-[0_1px_0_#E6E4DF]">
        {/* instrument strip */}
        <div className="mono flex flex-wrap items-center gap-[22px] bg-strip px-[18px] py-[9px] text-[12px] text-[#EDEBE6]">
          <span className="serif mr-0.5 text-[18px] text-white">densitygen</span>
          <span className="flex items-center gap-[7px] text-[#B9B6AF]">
            <span className="dot-pulse" />
            SURFACE SIM <b className="font-medium text-white">LIVE</b>
          </span>
          <span className="flex items-center gap-1.5 text-[#B9B6AF]">
            SYSTEM <b className="font-medium text-white">{m.pre.split("[")[0].split("(")[0]} / –OH</b>
          </span>
          <span className="ml-auto text-[#8C8980]">ALD half-cycle · ILLUSTRATIVE</span>
        </div>

        {/* head */}
        <div className="border-b border-hair px-5 pb-3 pt-4">
          <div className="mono text-[11px] uppercase tracking-[0.13em] text-faint">
            First half-reaction · precursor + surface –OH
          </div>
          <h1 className="display mt-[3px] text-[29px] leading-[1.1]">
            Surface chemistry, <span className="accent">in motion</span>
          </h1>
          <div className="mono mt-2.5 inline-block rounded-[2px] border border-hair bg-canvas px-[11px] py-[7px] text-[12.5px] text-ink2">
            {m.pre} + <span className="text-amber-deep">‖–O–H</span> → <span className="text-amber-deep">‖–O–{m.prod}</span> + {m.by}
          </div>
        </div>

        {/* body */}
        <div className="grid grid-cols-1 md:grid-cols-[1fr_318px]">
          {/* stage */}
          <div
            ref={stage}
            className="relative h-[452px] touch-none border-r border-hair"
            style={{ background: "radial-gradient(120% 100% at 50% 0%, #FFFFFF 0%, #FAFAF8 60%, #F2F1ED 100%)", cursor: "grab" }}
          >
            <div ref={glHost} className="absolute inset-0" />
            <div className="pointer-events-none absolute left-4 top-3.5 flex flex-col gap-[7px]">
              <span className="mono rounded-[2px] border border-hair bg-white/80 px-2 py-[3px] text-[10.5px] uppercase tracking-[0.06em] text-muted">
                STAGE <b ref={stageLabel} className="font-semibold text-amber-deep">APPROACH</b>
              </span>
              <span className="mono rounded-[2px] border border-hair bg-white/80 px-2 py-[3px] text-[10.5px] uppercase tracking-[0.06em] text-muted">
                M–O BOND <b ref={bondLabel} className="font-semibold text-muted">forming…</b>
              </span>
            </div>
            <div className="pointer-events-none absolute bottom-3 left-4 flex flex-wrap gap-[9px]">
              {[
                { c: "#B23B2E", l: "O" },
                { c: "#DCDAD2", l: "H" },
                { c: "#34332F", l: "C" },
                { c: m.color, l: m.sym },
              ].map((x) => (
                <span key={x.l} className="mono flex items-center gap-1.5 rounded-[2px] border border-hair bg-white/80 px-1.5 py-0.5 text-[10px] text-muted">
                  <span className="h-2 w-2 rounded-full" style={{ background: x.c }} />
                  {x.l}
                </span>
              ))}
              <span className="mono flex items-center gap-1.5 rounded-[2px] border border-amber-border bg-white/80 px-1.5 py-0.5 text-[10px] text-amber-deep">
                <span className="h-2 w-2 rounded-full bg-amber" />
                new bond
              </span>
            </div>
            <div className="mono pointer-events-none absolute bottom-3 right-4 text-[10px] text-faint">drag · scroll to zoom</div>
            <div ref={fallback} className="mono absolute inset-0 hidden items-center justify-center p-8 text-center text-[12px] text-muted">
              WebGL renderer unavailable in this browser.
            </div>
          </div>

          {/* numbers + energy */}
          <div className="flex flex-col p-4">
            <div className="mono text-[10px] uppercase tracking-[0.1em] text-faint">Predicted · {m.prodF}</div>
            <div className="mt-2 flex items-baseline gap-[7px]">
              <span className="serif text-[52px] leading-[0.9] text-ink">{m.Ea.toFixed(2)}</span>
              <span className="mono text-[14px] text-faint">eV</span>
            </div>
            <div className="mono mt-0.5 text-[10.5px] tracking-[0.04em] text-amber-deep">ACTIVATION BARRIER Eₐ</div>

            <div className="mt-3.5 grid grid-cols-2 gap-px overflow-hidden rounded-[2px] border border-hair bg-hair">
              <Stat v={m.dE.toFixed(1)} l="ΔE_rxn eV" />
              <Stat v={m.kappa} l="dielectric κ" />
              <Stat v={m.eg} l="band gap eV" />
              <Stat v={m.temp} l="window °C" />
            </div>

            <div className="mt-3.5 rounded-[2px] border border-hair bg-surface px-1 pb-0.5 pt-1.5">
              <div className="flex justify-between px-2">
                <span className="mono text-[10px] text-muted">REACTION COORDINATE</span>
                <span className="mono text-[10px] text-faint">schematic</span>
              </div>
              <svg viewBox="0 0 320 182" className="block h-auto w-full">
                <line x1={38} y1={pyE(0)} x2={306} y2={pyE(0)} stroke="var(--color-hair)" strokeWidth={1} strokeDasharray="3 2" />
                <line x1={38} y1={pyE(m.dE)} x2={306} y2={pyE(m.dE)} stroke="var(--color-amber-border)" strokeWidth={1} strokeDasharray="3 2" />
                <path d={curveD.trim()} fill="none" stroke="var(--color-ink2)" strokeWidth={1.8} />
                <line x1={pxi(0.5)} y1={pyE(m.Ea)} x2={pxi(0.5)} y2={pyE(0)} stroke="var(--color-amber)" strokeWidth={1} strokeDasharray="2 2" />
                <text x={pxi(0.5)} y={pyE(m.Ea)} dx={6} dy={4} fill="var(--color-amber-deep)" className="mono" fontSize={11}>
                  Eₐ {m.Ea.toFixed(2)}
                </text>
                <text x={300} y={pyE(m.dE)} dy={-4} fill="var(--color-amber-deep)" className="mono" fontSize={10} textAnchor="end">
                  ΔE {m.dE.toFixed(1)}
                </text>
                <text x={40} y={pyE(0)} dy={-4} fill="var(--color-faint)" className="mono" fontSize={9}>reactants</text>
                <circle ref={dot} cx={38} cy={pyE(0)} r={4.5} fill="var(--color-amber)" stroke="#fff" strokeWidth={1.5} />
              </svg>
              <div className="mono px-2 pb-1 text-right text-[10px] text-muted">
                E = <b ref={curE} className="text-ink">0.00</b> eV
              </div>
            </div>

            <div className="mono mt-2.5 text-[9.5px] leading-relaxed text-faint">
              UMA · OMat24-trained MLIP — <span className="text-amber-deep">predicted ±0.08 eV</span>, not DFT-confirmed
            </div>
            <button
              onClick={() => setEscalated(true)}
              className="btn-primary mt-2.5 w-full"
              disabled={escalated}
            >
              {escalated ? "✓ Queued — r²SCAN + NEB" : "Confirm with DFT →"}
            </button>
            {escalated && (
              <button onClick={() => router.push("/compute")} className="mono mt-1.5 text-[11px] text-amber-deep underline">
                view in compute dispatch →
              </button>
            )}
          </div>
        </div>

        {/* controls */}
        <div className="flex flex-wrap items-center gap-3.5 border-t border-hair bg-surface px-[18px] py-[11px]">
          <div className="inline-flex overflow-hidden rounded-[2px] border border-line">
            {SURFACE_SYSTEMS.map((x, i) => (
              <button
                key={x.prodF}
                onClick={() => {
                  setMat(i);
                  setEscalated(false);
                }}
                className="px-3 py-[7px] text-[12px] font-medium"
                style={{
                  borderRight: i < SURFACE_SYSTEMS.length - 1 ? "1px solid var(--color-hair)" : "none",
                  background: i === mat ? "var(--color-ink)" : "#fff",
                  color: i === mat ? "#fff" : "var(--color-muted)",
                }}
              >
                {x.prodF}
              </button>
            ))}
          </div>
          <button onClick={onPlay} className="btn-primary min-w-[128px]">
            {playing ? "❚❚ Pause" : tauPct >= 100 ? "↻ Replay" : "▶ Play reaction"}
          </button>
          <div className="flex min-w-[150px] flex-1 items-center gap-2.5">
            <label className="mono text-[10.5px] uppercase tracking-[0.08em] text-faint">τ</label>
            <input ref={slider} type="range" min={0} max={1000} defaultValue={0} className="flex-1" onInput={onScrub} />
            <span className="mono min-w-[40px] text-right text-[12px] text-ink">{tauPct}%</span>
          </div>
          <button onClick={onReset} className="btn-ghost">Reset view</button>
        </div>

        <div className="border-t border-hair bg-canvas px-5 pb-3.5 pt-2.5 text-[11.5px] leading-relaxed text-muted">
          <b className="text-ink2">Schematic.</b> Ball-and-stick trajectory authored for communication — not
          DFT-relaxed coordinates or MD. Switching precursor swaps the predicted MLIP energetics;{" "}
          <b className="text-ink2">Confirm with DFT</b> dispatches a real r²SCAN/NEB job.
        </div>
      </div>
    </div>
  );
}

function Stat({ v, l }: { v: string; l: string }) {
  return (
    <div className="bg-surface px-[11px] py-[9px]">
      <div className="serif text-[26px] leading-none text-ink">{v}</div>
      <div className="mono mt-0.5 text-[9.5px] text-faint">{l}</div>
    </div>
  );
}
