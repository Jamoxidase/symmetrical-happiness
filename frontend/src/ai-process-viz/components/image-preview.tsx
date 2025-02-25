"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { X, Download } from "lucide-react"
import { cn } from "@/lib/utils"

interface ImagePreviewProps {
  imageData: {
    base64: string
    type: string
    filename?: string
  }
  isModal?: boolean
  onOpen?: () => void
  onClose?: () => void
  className?: string
}

export function ImagePreview({ imageData, isModal = false, onOpen, onClose, className }: ImagePreviewProps) {
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose?.()
      }
    }

    if (isModal) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isModal, onClose])

  const handlePreviewClick = () => {
    onOpen?.()
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (scale > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && scale > 1) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e: React.WheelEvent) => {
    if (isModal) {
      e.preventDefault()
      const delta = e.deltaY * -0.01
      const newScale = Math.min(Math.max(1, scale + delta), 4)
      setScale(newScale)
    }
  }

  const handleDownload = () => {
    const link = document.createElement("a")
    link.href = `data:${imageData.type};base64,${imageData.base64}`
    link.download = imageData.filename || "image"
    link.click()
  }

  if (isModal) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div
          ref={modalRef}
          className="bg-[var(--bg-surface)] p-4 rounded-lg shadow-xl max-w-[90vw] max-h-[90vh] relative"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          <div className="absolute top-4 right-4 flex gap-2">
            <div
              onClick={handleDownload}
              className="p-2 hover:bg-[var(--bg-hover)] rounded-full transition-colors cursor-pointer"
            >
              <Download className="w-5 h-5 text-[var(--text-primary)]" />
            </div>
            <div
              onClick={onClose}
              className="p-2 hover:bg-[var(--bg-hover)] rounded-full transition-colors cursor-pointer"
            >
              <X className="w-5 h-5 text-[var(--text-primary)]" />
            </div>
          </div>
          <div className="overflow-hidden rounded-lg">
            <img
              src={`data:${imageData.type};base64,${imageData.base64}`}
              alt="Full view"
              className="max-w-full h-auto object-contain transition-transform cursor-move"
              style={{
                transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
              }}
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div onClick={handlePreviewClick} className={cn("cursor-pointer relative group/preview", className)}>
      <div className="absolute inset-0 bg-[var(--bg-surface)] opacity-0 group-hover/preview:opacity-100 transition-opacity" />
      <img
        src={`data:${imageData.type};base64,${imageData.base64}`}
        alt="Preview"
        className="h-32 w-auto object-contain rounded-l-md border border-[var(--border-color)] shadow-lg"
      />
    </div>
  )
}

