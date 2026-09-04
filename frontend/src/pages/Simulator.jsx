import React, { useState } from "react";
import { SCENARIOS } from "../utils/constants";
import { runScenario } from "../api/simulator";
import { ScenarioCard } from "../components/simulator/ScenarioCard";
import { PipelineProgress } from "../components/simulator/PipelineProgress";
import { SimulationOutput } from "../components/simulator/SimulationOutput";
import { DeepAuditModal } from "../components/audit/DeepAuditModal";
import { Play, RotateCcw, Sparkles, Zap } from "lucide-react";

export function Simulator() {
  const [selectedScenarioId, setSelectedScenarioId] = useState("winnable_clean");
  const [isRunning, setIsRunning] = useState(false);
  const [stepIndex, setStepIndex] = useState(-1);
  const [result, setResult] = useState(null);
  const [selectedDisputeId, setSelectedDisputeId] = useState(null);

  const selectedScenario = SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0];

  const handleRunScenario = async (scenarioId = selectedScenarioId) => {
    setSelectedScenarioId(scenarioId);
    setIsRunning(true);
    setResult(null);
    setStepIndex(0);

    const totalSteps = 7;
    for (let i = 0; i < totalSteps; i++) {
      setStepIndex(i);
      await new Promise((resolve) => setTimeout(resolve, 320));
    }

    try {
      const output = await runScenario(scenarioId);
      setResult(output);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setStepIndex(-1);
    setIsRunning(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-[#172033]">
              Interactive Webhook Scenario Simulator
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live Pipeline
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Dispatch synthetic payment dispute webhooks to observe deterministic scoring, consumer fairness gate, and legal UDIR packet generation.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          {result && (
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-200 shadow-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}

          <button
            type="button"
            disabled={isRunning}
            onClick={() => handleRunScenario(selectedScenarioId)}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-2 shadow-sm transition-all disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>{isRunning ? "Simulating Pipeline..." : `Simulate: ${selectedScenario.title.split('.')[1]?.trim() || selectedScenario.title}`}</span>
          </button>
        </div>
      </div>

      {/* Preset Scenarios Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Select Test Scenario Case
          </span>
          <span className="text-[11px] text-slate-400">
            Click any case to load its physical courier telemetry payload
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {SCENARIOS.map((sc) => (
            <ScenarioCard
              key={sc.id}
              scenario={sc}
              isSelected={selectedScenarioId === sc.id}
              isRunning={isRunning && selectedScenarioId === sc.id}
              onSelect={() => setSelectedScenarioId(sc.id)}
            />
          ))}
        </div>
      </div>

      {/* Split View: Progression Stepper & Output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Pipeline Progression Stepper */}
        <PipelineProgress
          currentStepIndex={stepIndex}
          isRunning={isRunning}
          pipelineSteps={result?.pipelineSteps}
        />

        {/* Evaluation Output Summary */}
        <div>
          {result ? (
            <SimulationOutput
              result={result}
              onOpenAudit={(id) => setSelectedDisputeId(id)}
            />
          ) : (
            <div className="h-full min-h-[340px] rounded-xl border border-dashed border-slate-200 bg-white p-8 flex flex-col items-center justify-center text-center space-y-3 shadow-xs">
              <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                <Sparkles className="w-6 h-6 text-emerald-600" />
              </div>
              <div className="space-y-1 max-w-sm">
                <h4 className="text-xs font-bold text-[#172033]">
                  Ready to Dispatch Scenario
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Currently selected: <strong className="text-slate-700">{selectedScenario.title}</strong>. Click the green button above to trigger the 7-stage deterministic arbitration engine.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Deep Audit Modal */}
      <DeepAuditModal
        disputeId={selectedDisputeId}
        isOpen={Boolean(selectedDisputeId)}
        onClose={() => setSelectedDisputeId(null)}
      />
    </div>
  );
}
