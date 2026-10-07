import Image from "next/image";

type Visual = "dashboard" | "assistant" | "monitoring" | "symptoms" | "history" | "profile";

const visuals: Record<Visual, { src: string; width: number; height: number }> = {
  dashboard: { src: "/visual-dashboard-overview.svg", width: 520, height: 340 },
  assistant: { src: "/visual-clinical-chat.svg", width: 520, height: 340 },
  monitoring: { src: "/visual-vitals-monitor.svg", width: 520, height: 340 },
  symptoms: { src: "/visual-symptom-notes.svg", width: 520, height: 340 },
  history: { src: "/visual-health-history.svg", width: 520, height: 340 },
  profile: { src: "/visual-profile-wellbeing.svg", width: 520, height: 340 },
};

export default function PageVisual({ visual, className = "" }: { visual: Visual; className?: string }) {
  const asset = visuals[visual];

  return (
    <div className={`page-visual ${className}`} aria-hidden="true">
      <Image
        src={asset.src}
        alt=""
        width={asset.width}
        height={asset.height}
        className="h-auto w-full"
      />
    </div>
  );
}
