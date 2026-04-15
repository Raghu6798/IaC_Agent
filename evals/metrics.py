from deepeval.metrics import (
    TaskCompletionMetric,
    ToolCorrectnessMetric,
    ArgumentCorrectnessMetric,
    StepEfficiencyMetric,
    PlanAdherenceMetric,
    PlanQualityMetric,
    ConversationCompletenessMetric
)


task_completion_metric = TaskCompletionMetric()
tool_correctness_metric = ToolCorrectnessMetric()
argument_correctness_metric = ArgumentCorrectnessMetric()
step_efficiency_metric = StepEfficiencyMetric()
plan_adherence_metric = PlanAdherenceMetric()
plan_quality_metric = PlanQualityMetric()
conversation_completeness_metric = ConversationCompletenessMetric()
