export type StepStatus = "active" | "completed"

export interface ToolProgress {
  id: string
  name: string
  status: "start" | "end" | "update"
  content: string
  file?: string
  imageData?: {
    base64: string
    type: string
    filename?: string
  }
}

export interface Step {
  id: string
  content: string
  status: StepStatus
  tools: ToolProgress[]
}

export type StreamChunk =
  | { type: "execute_plan"; content: string; timestamp: string }
  | {
      type: "tool_progress_GtRNAdb" | "tool_progress_gtrnadb" | "tool_progress_genome"
      status: "start" | "end" | "update"
      content: string
      timestamp: string
      file?: string
      imageData?: {
        base64: string
        type: string
        filename?: string
      }
    }
  | { type: "start_response"; timestamp: string }

