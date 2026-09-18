type Prediction = {
  condition: string;
  risk_level: "Low" | "Moderate" | "High" | string;
  contributing_factors: string[];
  probability_percent?: number | null;
  algorithm_used?: string;
  input_coverage_percent?: number | null;
  assumed_features?: string[];
};

const RISK_CLASS: Record<string, string> = {
  Low: "risk-low",
  Moderate: "risk-moderate",
  High: "risk-high",
};

export default function RiskCard({ prediction }: { prediction: Prediction }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800">{prediction.condition}</h3>
        <span
          className={`text-xs font-semibold px-3 py-1 rounded-full ${
            RISK_CLASS[prediction.risk_level] || "bg-gray-100 text-gray-600"
          }`}
        >
          {prediction.risk_level} Risk
        </span>
      </div>

      {prediction.probability_percent != null && (
        <p className="text-sm text-gray-500 mb-2">
          Estimated likelihood: <strong>{prediction.probability_percent}%</strong>
        </p>
      )}

      {prediction.input_coverage_percent != null && (
        <details className="mb-3 rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600">
          <summary className="cursor-pointer font-medium text-gray-700">
            {prediction.input_coverage_percent}% of model inputs came from your data
          </summary>
          {prediction.assumed_features && prediction.assumed_features.length > 0 ? (
            <p className="mt-2 leading-5">
              The remaining clinical inputs use training-data median values: {prediction.assumed_features.join(", ")}.
            </p>
          ) : (
            <p className="mt-2 leading-5">All model inputs were available from your data.</p>
          )}
        </details>
      )}

      <p className="text-xs uppercase tracking-wide text-gray-400 mb-1">Factors to discuss</p>
      <p className="mb-2 text-xs leading-4 text-gray-500">These are model inputs above its comparison baseline, not proven causes.</p>
      <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
        {prediction.contributing_factors.map((f, i) => (
          <li key={i}>{f}</li>
        ))}
      </ul>
    </div>
  );
}
