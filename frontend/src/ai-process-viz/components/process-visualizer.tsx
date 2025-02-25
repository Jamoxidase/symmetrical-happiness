"use client"

import type React from "react"

import { useReducer, useState, forwardRef, useImperativeHandle } from "react"
import { ChevronDown, ChevronRight, ImageIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Step, StreamChunk, ToolProgress } from "../types"
import { ImagePreview } from "./image-preview"

function processReducer(state: Step[], action: StreamChunk): Step[] {
  switch (action.type) {
    case "execute_plan":
      return [
        ...state.map((step) => ({ ...step, status: "completed" })),
        { id: `step-${state.length + 1}`, content: action.content, status: "active", tools: [] },
      ]
    case "tool_progress_GtRNAdb":
    case "tool_progress_gtrnadb":
    case "tool_progress_genome":
      if (state.length === 0) return state
      const lastStep = state[state.length - 1]
      const toolName = action.type.replace("tool_progress_", "")
      // Don't create a tool progress item for image updates
      if (action.type === "tool_progress_genome" && action.status === "update" && action.file === "image") {
        return state;
      }

      const newTool: ToolProgress = {
        id: `tool-${lastStep.tools.length + 1}`,
        name: toolName,
        status: action.status,
        content: action.content,
      }

      return [
        ...state.slice(0, -1),
        {
          ...lastStep,
          tools: [...lastStep.tools, newTool],
        },
      ]
    case "start_response":
      // Mark all steps as completed
      return state.map((step) => ({ ...step, status: "completed" }))
    default:
      return state
  }
}

interface StepItemProps {
  step: Step
  isLast: boolean
  expandedSteps: Set<string>
  onToggleStep: (stepId: string) => void
}

function StepItem({ step, isLast, expandedSteps, onToggleStep }: StepItemProps) {
  const isExpanded = expandedSteps.has(step.id)
  const isExpandable = step.tools.length > 0
  const isActive = step.status === "active"

  return (
    <div className="relative">
      {/* Vertical line for the step */}
      <div
        className={cn("absolute left-[2px] top-0 w-[1px]", isLast ? "h-full" : "h-full", "bg-[var(--border-color)]")}
      />

      <button
        onClick={(e) => {
          e.stopPropagation()
          if (isExpandable) onToggleStep(step.id)
        }}
        className={cn(
          "w-full text-left group transition-colors duration-150",
          "hover:bg-[var(--bg-hover)] rounded-md px-2 -mx-2",
          isExpandable && "cursor-pointer",
          "relative overflow-hidden",
        )}
      >
        <div className="flex items-center gap-2 py-1 relative">
          <div
            className={cn(
              "w-[5px] h-[5px] rounded-full relative z-10 ",
              isActive ? "bg-[var(--accent-color)]" : "bg-[var(--border-color)]",
            )}
          />

          <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1">
              <h3 className={cn("text-sm truncate text-[var(--text-primary)]", isActive && "animate-pulse")}>
                {step.content}
              </h3>
            </div>

            {isExpandable && (
              <div
                className={cn(
                  "opacity-0 group-hover:opacity-100 transition-opacity duration-150",
                  isExpanded && "opacity-100",
                )}
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)]" />
                )}
              </div>
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="pl-4 space-y-1 mt-1 relative">
          {/* Vertical line for child items */}
          
          {step.tools.map((tool, index) => (
            <ToolProgressItem key={tool.id} tool={tool} isLast={index === step.tools.length - 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function ToolProgressItem({ tool, isLast }: { tool: ToolProgress; isLast: boolean }) {
  return (
    <div className="flex items-center gap-2 py-1 relative">
      {/* Horizontal connector line */}
      <div className="absolute left-[-14px] top-[50%] w-3 h-[1px] bg-[var(--border-color)]" />
      <div
        className={cn(
          "w-[3px] h-[3px] rounded-full relative z-10",
          tool.status === "start" ? "bg-[var(--accent-color)]" : "bg-[var(--border-color)]",
        )}
      />
      <div className="text-xs text-[var(--text-tertiary)]">{tool.content}</div>
    </div>
  )
}

export interface ProcessVisualizerRef {
  handleChunk: (chunk: StreamChunk) => void
}

export const ProcessVisualizer = forwardRef<ProcessVisualizerRef>((_, ref) => {
  const [steps, dispatch] = useReducer(processReducer, [])
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [isHeaderExpanded, setIsHeaderExpanded] = useState(true)
  const [currentImage, setCurrentImage] = useState<ToolProgress["imageData"]>()
  const [isImageModalOpen, setIsImageModalOpen] = useState(false)

  const handleChunk = (chunk: StreamChunk) => {
    if (chunk.type === "start_response") {
      setIsHeaderExpanded(false)
      setExpandedSteps(new Set())
    } else if (chunk.type === "execute_plan") {
      setExpandedSteps((prev) => {
        const newSet = new Set(prev)
        newSet.add(`step-${steps.length + 1}`)
        return newSet
      })
    } else if (chunk.type === "tool_progress_genome" && chunk.status === "update" && chunk.file === "image") {
      // Convert the base64 string to proper image data format
      setCurrentImage({
        base64: chunk.content,
        type: "image/png"
      })
    }
    dispatch(chunk)
  }

  const toggleHeader = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsHeaderExpanded(!isHeaderExpanded)
  }

  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev)
      if (next.has(stepId)) {
        next.delete(stepId)
      } else {
        next.add(stepId)
      }
      return next
    })
  }

  useImperativeHandle(ref, () => ({
    handleChunk,
  }))

  return (
    <div className="relative w-3/4 mx-auto">
      <div className="bg-[var(--bg-surface)] bg-opacity-80 backdrop-blur-sm rounded-lg p-3 text-[var(--text-primary)] border border-[var(--border-color)] relative z-10">
        <div
          className="flex items-center justify-between hover:bg-[var(--bg-hover)] rounded-md px-2 -mx-2 py-1 cursor-pointer"
          onClick={toggleHeader}
        >
          <h2 className="text-sm font-medium">Process Feedback</h2>
          <div className="flex items-center gap-2">
            {!isHeaderExpanded && currentImage && (
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  setIsImageModalOpen(true)
                }}
                className="p-1 hover:bg-[var(--bg-hover)] rounded-full transition-colors cursor-pointer"
              >
                <ImageIcon className="w-4 h-4 text-[var(--text-tertiary)]" />
              </div>
            )}
            <div className={cn("transition-opacity duration-150", !isHeaderExpanded && "opacity-100")}>
              {isHeaderExpanded ? (
                <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
              ) : (
                <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)]" />
              )}
            </div>
          </div>
        </div>

        <div
          className={cn(
            "grid transition-[grid-template-rows] duration-200",
            isHeaderExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
          )}
        >
          <div className="overflow-hidden">
            {steps.length > 0 && (
              <div className="space-y-1 mt-2">
                {steps.map((step, index) => (
                  <StepItem
                    key={step.id}
                    step={step}
                    isLast={index === steps.length - 1}
                    expandedSteps={expandedSteps}
                    onToggleStep={toggleStep}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {currentImage && isHeaderExpanded && (
        <div
          className={cn(
            "absolute top-0 right-0 h-32 transform transition-all duration-300 z-0",
            "translate-x-[calc(10%)] hover:translate-x-full",
          )}
          onClick={() => setIsImageModalOpen(true)} // Add click handler here
        >
          <ImagePreview
            imageData={currentImage}
            onOpen={() => setIsImageModalOpen(true)}
            className="pointer-events-none"
          />
        </div>
      )}

      {isImageModalOpen && currentImage && (
        <ImagePreview imageData={currentImage} isModal={true} onClose={() => setIsImageModalOpen(false)} />
      )}
    </div>
  )
})

ProcessVisualizer.displayName = "ProcessVisualizer"

