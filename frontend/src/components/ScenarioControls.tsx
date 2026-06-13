import { useState } from "react";

import type { ScenarioAssumptions, ScenarioName, StagingBasis } from "../types/portfolio";
import { SCENARIO_LABELS, STAGING_BASIS_LABELS } from "../types/portfolio";

interface Props {
  scenarios: ScenarioAssumptions;
  onApply: (scenarios: ScenarioAssumptions) => void;
}

const SCENARIO_ORDER: ScenarioName[] = ["base", "upside", "downside"];

export function ScenarioControls({ scenarios, onApply }: Props) {
  const [draft, setDraft] = useState<ScenarioAssumptions>(scenarios);

  const totalWeight = draft.base.weight + draft.upside.weight + draft.downside.weight;
  const error =
    Math.abs(totalWeight - 1) > 1e-6
      ? `Scenario weights must sum to 100% (currently ${Math.round(totalWeight * 100)}%).`
      : null;

  const isDirty = JSON.stringify(draft) !== JSON.stringify(scenarios);

  function updateScenario(name: ScenarioName, field: "weight" | "pd_multiplier", value: number) {
    setDraft({ ...draft, [name]: { ...draft[name], [field]: value } });
  }

  function handleApply() {
    if (error) return;
    onApply(draft);
  }

  return (
    <div className="scenario-controls">
      <label className="scenario-toggle">
        <input
          type="checkbox"
          checked={draft.enabled}
          onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })}
        />
        Weight ECL across macroeconomic scenarios
      </label>

      <div className={`scenario-controls-body${draft.enabled ? "" : " disabled"}`}>
        {SCENARIO_ORDER.map((name) => (
          <div className="scenario-field-group" key={name}>
            <div className="scenario-field-group-label">{SCENARIO_LABELS[name]}</div>
            <div className="staging-field">
              <label htmlFor={`${name}-weight`}>Weight</label>
              <input
                id={`${name}-weight`}
                type="number"
                min={0}
                max={1}
                step={0.05}
                disabled={!draft.enabled}
                value={draft[name].weight}
                onChange={(e) => updateScenario(name, "weight", Number(e.target.value))}
              />
            </div>
            <div className="staging-field">
              <label htmlFor={`${name}-multiplier`}>PD multiplier</label>
              <input
                id={`${name}-multiplier`}
                type="number"
                min={0}
                step={0.1}
                disabled={!draft.enabled}
                value={draft[name].pd_multiplier}
                onChange={(e) => updateScenario(name, "pd_multiplier", Number(e.target.value))}
              />
            </div>
          </div>
        ))}
        <div className="staging-field">
          <label>SICR test uses</label>
          <div className="staging-basis-toggle" role="radiogroup" aria-label="SICR test uses">
            {Object.entries(STAGING_BASIS_LABELS).map(([value, label]) => (
              <label
                key={value}
                className={`staging-basis-option${draft.staging_basis === value ? " active" : ""}`}
              >
                <input
                  type="radio"
                  name="staging-basis"
                  value={value}
                  disabled={!draft.enabled}
                  checked={draft.staging_basis === value}
                  onChange={() => setDraft({ ...draft, staging_basis: value as StagingBasis })}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      </div>

      <button type="button" className="link-button" onClick={handleApply} disabled={!isDirty || !!(draft.enabled && error)}>
        Apply
      </button>
      {draft.enabled && error && <div className="staging-error">{error}</div>}
    </div>
  );
}
