import { isProcessingReport, elapsedSeconds, statusStepLabel } from '../utils/reportStatus.js'

export default function ReportProgressHint({ report, tick }) {
  if (!isProcessingReport(report)) return null
  void tick

  return (
    <div className="mt-1 space-y-0.5 text-xs text-zinc-500">
      <div className="text-zinc-400">{statusStepLabel(report.status)}</div>
      <div>已等候 {elapsedSeconds(report.created_at)} 秒</div>
    </div>
  )
}
