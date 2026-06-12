import { useState } from "react";

import type { StagingAssumptions } from "../types/portfolio";

interface Props {
  staging: StagingAssumptions;
  onApply: (staging: StagingAssumptions) => void;
}

export function StagingControls({ staging, onApply }: Props) {
  const [draft, setDraft] = useState<StagingAssumptions>(staging);

  const error =
    draft.stage_3_dpd_threshold < draft.stage_2_dpd_threshold
      ? "Stage 3 backstop must be greater than or equal to the stage 2 backstop."
      : null;

  const isDirty =
    draft.sicr_pd_multiple !== staging.sicr_pd_multiple ||
    draft.stage_2_dpd_threshold !== staging.stage_2_dpd_threshold ||
    draft.stage_3_dpd_threshold !== staging.stage_3_dpd_threshold;

  function handleApply() {
    if (error) return;
    onApply(draft);
  }

  return (
    <div className="staging-controls">
      <div className="staging-field">
        <label htmlFor="sicr-multiple">SICR PD multiple</label>
        <input
          id="sicr-multiple"
          type="number"
          min={0}
          step={0.1}
          value={draft.sicr_pd_multiple}
          onChange={(e) => setDraft({ ...draft, sicr_pd_multiple: Number(e.target.value) })}
        />
      </div>
      <div className="staging-field">
        <label htmlFor="stage-2-dpd">Stage 2 DPD backstop</label>
        <input
          id="stage-2-dpd"
          type="number"
          min={0}
          step={1}
          value={draft.stage_2_dpd_threshold}
          onChange={(e) => setDraft({ ...draft, stage_2_dpd_threshold: Number(e.target.value) })}
        />
      </div>
      <div className="staging-field">
        <label htmlFor="stage-3-dpd">Stage 3 DPD backstop</label>
        <input
          id="stage-3-dpd"
          type="number"
          min={0}
          step={1}
          value={draft.stage_3_dpd_threshold}
          onChange={(e) => setDraft({ ...draft, stage_3_dpd_threshold: Number(e.target.value) })}
        />
      </div>
      <button type="button" className="link-button" onClick={handleApply} disabled={!isDirty || !!error}>
        Apply
      </button>
      {error && <div className="staging-error">{error}</div>}
    </div>
  );
}
