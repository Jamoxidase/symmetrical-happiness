import { cn } from "@/lib/utils"
import { forwardRef } from "react"

const Alert = forwardRef(({ className, variant = "default", ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(
      "relative w-full rounded-lg border px-4 py-3 text-sm",
      variant === "default" && "bg-background text-foreground",
      variant === "destructive" &&
        "border-destructive/50 text-destructive dark:border-destructive",
      className
    )}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertDescription = forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertDescription }