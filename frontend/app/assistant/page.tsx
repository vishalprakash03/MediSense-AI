"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ChatBubble from "@/components/ChatBubble";
import RiskCard from "@/components/RiskCard";
import Disclaimer from "@/components/Disclaimer";
import WellbeingPlan from "@/components/WellbeingPlan";
import { getToken, sendChatMessage, predictRisk } from "@/services/api";

type Msg = { role: "user" | "assistant"; text: string };

export default function AssistantPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [sending, setSending] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [unavailablePredictions, setUnavailablePredictions] = useState<any[]>([]);
  const [overallRisk, setOverallRisk] = useState<string | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [chatError, setChatError] = useState("");
  const [predictionError, setPredictionError] = useState("");
  const [recommendations, setRecommendations] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const answerCount = messages.filter((message) => message.role === "user").length;
  const currentStage = answerCount < 6 ? 1 : answerCount < 13 ? 2 : 3;

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    // Kick off the conversation with an empty message to receive the greeting.
    sendChatMessage("")
      .then((res) => {
        setSessionId(res.data.session_id);
        setMessages([{ role: "assistant", text: res.data.reply }]);
      })
      .catch(() => setChatError("We couldn’t start the assessment. Check the connection and refresh the page."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userText = input.trim();
    setChatError("");
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setInput("");
    setSending(true);
    try {
      const res = await sendChatMessage(userText, sessionId);
      setMessages((m) => [...m, { role: "assistant", text: res.data.reply }]);
      if (res.data.is_complete) {
        setIsComplete(true);
        runPrediction(res.data.collected_answers);
      }
    } catch (err: any) {
      setChatError(err?.response?.data?.detail || "Your answer could not be sent. Please try again.");
    } finally {
      setSending(false);
    }
  }

  async function runPrediction(answers: any) {
    setPredicting(true);
    setPredictionError("");
    try {
      const res = await predictRisk(answers);
      setPredictions(res.data.predicted_conditions);
      setUnavailablePredictions(res.data.unavailable_predictions || []);
      setOverallRisk(res.data.overall_risk);
      setRecommendations(res.data.recommendations || null);
    } catch (err: any) {
      setPredictionError(
        err?.response?.data?.detail || "We couldn’t complete the risk assessment. Please try again later."
      );
    } finally {
      setPredicting(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex max-w-4xl flex-1 flex-col p-5 pt-20 md:p-8">
        <section className="mb-5 rounded-3xl bg-gradient-to-r from-slate-900 via-brand-700 to-brand-500 px-6 py-7 text-white shadow-lg shadow-brand-900/10">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-100">Private guided assessment</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Let&apos;s understand your health picture.</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-brand-50">Answer one question at a time. You can skip clinical readings you do not know, and we will be clear about what needs more information.</p>
        </section>

        <div className="mb-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-700">Guided intake</p>
            <p className="text-xs text-slate-500">Moves forward as you answer</p>
          </div>
          <div className="mt-3 grid gap-2 text-xs sm:grid-cols-3">
            <ProgressStage number={1} label="Health background" active={currentStage === 1} complete={currentStage > 1} />
            <ProgressStage number={2} label="Measurements" active={currentStage === 2} complete={currentStage > 2} />
            <ProgressStage number={3} label="Symptoms & doctor note" active={currentStage === 3} complete={isComplete} />
          </div>
        </div>

        <div className="card mb-5 flex flex-1 flex-col border-slate-100 shadow-md" style={{ minHeight: "420px" }}>
          <div className="flex-1 overflow-y-auto pr-1" style={{ maxHeight: "50vh" }}>
            {messages.map((m, i) => (
              <ChatBubble key={i} role={m.role} text={m.text} />
            ))}
            <div ref={bottomRef} />
          </div>

          {!isComplete && (
            <>
              {chatError && <p className="mt-4 text-sm text-red-600" role="alert">{chatError}</p>}
              <form onSubmit={handleSend} className="mt-4 flex gap-2 border-t pt-4">
                <input
                  className="input-field"
                  placeholder="Type your response here…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={sending}
                />
                <button className="btn-primary" disabled={sending || !input.trim()}>
                  Send
                </button>
              </form>
              <p className="mt-2 text-xs text-slate-400">Please do not use this chat for emergency symptoms. Seek urgent medical help instead.</p>
            </>
          )}
        </div>

        {isComplete && (
          <div className="space-y-4">
            <Disclaimer />
            {predicting ? (
              <p className="text-sm text-gray-500">Analyzing your health data…</p>
            ) : predictionError ? (
              <p className="text-sm text-red-600" role="alert">{predictionError}</p>
            ) : (
              <>
                {predictions.length > 0 && (
                  <>
                    <div className="card flex items-center justify-between">
                      <span className="text-sm text-gray-500">Overall Health Risk</span>
                      <span className={`text-sm font-semibold px-3 py-1 rounded-full ${overallRisk === "High" ? "risk-high" :
                        overallRisk === "Moderate" ? "risk-moderate" : "risk-low"
                        }`}>
                        {overallRisk}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {predictions.map((p, i) => (
                        <RiskCard key={i} prediction={p} />
                      ))}
                    </div>
                  </>
                )}

                {unavailablePredictions.length > 0 && (
                  <div className="card">
                    <h2 className="font-semibold text-gray-800">Assessments needing more information</h2>
                    <div className="mt-3 space-y-3">
                      {unavailablePredictions.map((item, index) => (
                        <div key={index} className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm">
                          <p className="font-medium text-amber-900">{item.condition}</p>
                          <p className="mt-1 text-amber-800">{item.reason}</p>
                          {item.missing_inputs?.length > 0 && (
                            <p className="mt-1 text-amber-800">
                              Missing: {item.missing_inputs.join(", ")}.
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <WellbeingPlan recommendations={recommendations} />

                {predictions.length === 0 && unavailablePredictions.length === 0 && (
                  <p className="text-sm text-gray-500">
                    No trained models are available yet on the server. Ask your administrator to run
                    the ML training pipeline.
                  </p>
                )}
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function ProgressStage({ number, label, active, complete }: { number: number; label: string; active: boolean; complete: boolean }) {
  return (
    <div className={`flex items-center gap-2 rounded-xl px-3 py-2.5 ${active ? "bg-brand-50 font-medium text-brand-800" : complete ? "bg-green-50 text-green-800" : "bg-slate-50 text-slate-500"}`}>
      <span className={`grid h-5 w-5 place-items-center rounded-full text-[10px] font-semibold ${active ? "bg-brand-600 text-white" : complete ? "bg-green-600 text-white" : "bg-slate-200 text-slate-600"}`}>{complete ? "✓" : number}</span>
      <span>{label}</span>
    </div>
  );
}
