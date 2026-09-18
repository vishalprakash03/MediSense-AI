export default function ChatBubble({ role, text }: { role: "user" | "assistant"; text: string }) {
  const isUser = role === "user";
  return (
    <div className={`flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && <span className="mb-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-100 text-sm">🩺</span>}
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 whitespace-pre-wrap shadow-sm ${
          isUser
            ? "rounded-br-sm bg-brand-600 text-white"
            : "rounded-bl-sm border border-slate-100 bg-slate-50 text-slate-800"
        }`}
      >
        {text}
      </div>
      {isUser && <span className="mb-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-slate-200 text-xs text-slate-600">You</span>}
    </div>
  );
}
