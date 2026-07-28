import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import type { ModelInfoResponse } from '../../common/types'

/** A "model card": what the currently-cached forecasting model actually is, trained on what data, and when. */
export function ModelInfoPanel() {
  const { data, error, isLoading } = useApiData<ModelInfoResponse>('/api/forecasting/model-info', 0)
  const hasData = Boolean(data)

  return (
    <ChartCard
      title="How this model is built"
      isLoading={isLoading}
      hasData={hasData}
      error={error}
    >
      {data && (
        <div className="flex flex-col gap-4 text-sm text-slate-700 dark:text-slate-300">
          <p>{data.algorithm}</p>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
            <dt className="text-slate-500 dark:text-slate-400">Trained on</dt>
            <dd>
              {data.trainingWindowStart} → {data.trainingWindowEnd}
            </dd>
            <dt className="text-slate-500 dark:text-slate-400">Training rows</dt>
            <dd>{data.trainingRowCount.toLocaleString()}</dd>
            <dt className="text-slate-500 dark:text-slate-400">Last trained</dt>
            <dd>{new Date(data.trainedAt).toLocaleString()}</dd>
            <dt className="text-slate-500 dark:text-slate-400">Quantiles</dt>
            <dd>{data.quantiles.map((q) => `p${q * 100}`).join(', ')}</dd>
          </dl>

          <div>
            <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">Features</p>
            <ul className="list-disc space-y-1 pl-5">
              {data.features.map((feature) => (
                <li key={feature.name}>
                  <code className="text-xs">{feature.name}</code> — {feature.description}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </ChartCard>
  )
}
