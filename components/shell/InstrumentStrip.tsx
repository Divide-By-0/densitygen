import { JOBS } from "@/lib/data/jobs";

export function InstrumentStrip() {
  const nQueue = JOBS.filter((j) => j.st === "queued").length;
  return (
    <div className="mono flex flex-shrink-0 items-center gap-[22px] border-b border-black bg-strip px-[18px] py-2 text-[12px] text-[#EDEBE6]">
      <span className="serif mr-0.5 text-[20px] tracking-[0.01em] text-white">densitygen</span>
      <span className="flex items-center gap-[7px] text-[#B9B6AF]">
        <span className="dot-pulse" />
        SYS <b className="font-medium text-white">NOMINAL</b>
      </span>
      <span className="hidden items-center gap-1.5 text-[#B9B6AF] sm:flex">
        RUNS <b className="font-medium text-white">1,284</b>
      </span>
      <span className="hidden items-center gap-1.5 text-[#B9B6AF] sm:flex">
        QUEUE <b className="font-medium text-white">{nQueue}</b>
      </span>
      <span className="hidden items-center gap-1.5 text-[#B9B6AF] md:flex">
        CORE·HRS <b className="font-medium text-white">184K / 500K</b>
      </span>
      <span className="ml-auto flex items-center gap-4 text-[#8C8980]">
        <span className="hidden lg:inline">
          CAMPAIGN <b className="font-medium text-[#EDEBE6]">Q3-HIGHK-04</b>
        </span>
        <span className="hidden md:inline">14:22:07 PT</span>
        <span className="flex h-[22px] w-[22px] items-center justify-center rounded-full bg-[#3C3B38] text-[11px] text-[#EDEBE6]">
          KP
        </span>
      </span>
    </div>
  );
}
